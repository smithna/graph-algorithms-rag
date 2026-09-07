"""Entity embedding for the four labels that need vectors — and only those.

Reworked from the corps repo's ``embed_entities.py`` (which stays untouched and
authoritative for its own pipeline). Two decisions, both measured against the
question bank rather than assumed (outline: "Design notes", 2026-09-07):

**Only AnimalSpecies, PlantSpecies, Taxon, and Event are embedded.** These are
the labels where a build step *replaced* the user's vocabulary with a canonical
one — ``add_taxonomy.py`` renamed animals and plants to Latin binomials
("grizzly bear" shares no token with URSUS ARCTOS HORRIBILIS), and Event
queries are paraphrases of descriptive names ("a baby born on the trip" vs
BIRTH OF CHARBONNEAU'S SON). Person, Place, WaterBody, and NativeNation are
queried by name in every demo question; fuzzy fulltext over name + aliases is
the right tool there, and disambiguation folded the descriptive Person forms
("Interpreters Wife", "Janey") into aliases where fulltext can see them.
A person_embeddings fallback for pure-paraphrase person queries is noted in
the outline as an idea for later — deliberately not built here.

**No boilerplate sentence, no glosses.** The corps script wrapped every name in
the same clause ("person associated with the Lewis and Clark Expedition..."),
which for short names was most of the tokens — every vector shared a large
common component, similarity floors rose by construction, and absolute cutoffs
went meaningless. It turns out nothing of the sort is needed for these four
labels: Event names are descriptive phrases already, Taxon descriptions
aggregate descendant common names (a corpus-derived gloss, no LLM), and
binomials are globally-attested identifiers the embedding model knows on its
own — the archaic journal aliases ("LARGE BLUE CRESTED CORVUS" for Steller's
jay) then add the corpus's own vocabulary on top. A one-word type cue survives
for the names that read as common nouns without it.

Usage:
  python tools/embed_entities.py --dry-run              # print samples, no writes
  python tools/embed_entities.py                        # embed + write + index
  python tools/embed_entities.py --reindex-only         # indexes only
  python tools/embed_entities.py --database lewisclark  # default
"""
import argparse
import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field

sys.path.insert(0, "/Users/nathansmith/Documents/kcdc-2026/graph-algorithms-rag")

ap = argparse.ArgumentParser()
ap.add_argument("--database", default="lewisclark")
ap.add_argument("--dry-run", action="store_true",
                help="print sample descriptions; no embedding, no writes")
ap.add_argument("--reindex-only", action="store_true",
                help="create per-label vector indexes without re-embedding")
a = ap.parse_args()
os.environ["NEO4J_DATABASE"] = a.database

from graphrank.config import driver, query, read_query, settings

EMBED_BATCH_SIZE = 100
WRITE_BATCH_SIZE = 200
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))

#: The embedded labels and their one-word type cues. The cue exists for names
#: that read as common nouns bare ("ATTEMPTED THEFT OF SPOON" does not need it;
#: "ROBIN" and "MOLE" do). One word — the per-label indexes carry the
#: discrimination, so a shared clause here buys nothing and costs geometry.
EMBED_LABELS = {
    "AnimalSpecies": "animal",
    "PlantSpecies": "plant",
    "Event": "event",
}

LABEL_INDEXES = {
    "AnimalSpecies": "animalspecies_embeddings",
    "PlantSpecies": "plantspecies_embeddings",
    "Event": "event_embeddings",
    "Taxon": "taxon_embeddings",
}

MAX_ALIASES = 8
MAX_TAXON_ALIASES = 12


@dataclass
class EntityRecord:
    element_id: str
    label: str
    canonical_name: str
    display_name: str
    aliases: list[str] = field(default_factory=list)
    taxon_rank: str = ""
    description: str = ""
    embedding: list[float] = field(default_factory=list)


def _clean_aliases(rec: EntityRecord, cap: int) -> list[str]:
    """Case-insensitive dedupe, canonical/display excluded, capped."""
    seen = {rec.canonical_name.upper(), rec.display_name.upper()}
    out: list[str] = []
    for alias in rec.aliases:
        alias = alias.strip()
        if alias and len(alias) > 1 and alias.upper() not in seen:
            seen.add(alias.upper())
            out.append(alias)
    return out[:cap]


def build_description(rec: EntityRecord) -> str:
    """<DisplayName> (<cue>)[. Also known as: ...] — and nothing else."""
    cue = EMBED_LABELS[rec.label]
    base = f"{rec.display_name} ({cue})"
    aliases = _clean_aliases(rec, MAX_ALIASES)
    if aliases:
        base += ". Also known as: " + ", ".join(aliases)
    return base


def build_taxon_description(rec: EntityRecord) -> str:
    """<Name> (<rank>)[. Species known as: ...].

    The alias rollup from descendant species is the whole value of a Taxon
    embedding — "salmon" has no lexical relationship to SALMONIDAE, and these
    aggregated common names exist nowhere on the node for fulltext to find.
    """
    rank = rec.taxon_rank or "taxon"
    base = f"{rec.display_name} ({rank})"
    aliases = _clean_aliases(rec, MAX_TAXON_ALIASES)
    if aliases:
        base += ". Species known as: " + ", ".join(aliases)
    return base


def fetch_entities() -> list[EntityRecord]:
    labels_union = "|".join(EMBED_LABELS)
    rows = read_query(
        f"""
        MATCH (n:{labels_union})
        WHERE NOT n:GenericLocation
        RETURN elementId(n) AS eid,
               [x IN labels(n) WHERE x IN $labels][0] AS label,
               coalesce(n.canonicalName, n.name, '') AS canonical_name,
               coalesce(n.name, n.canonicalName, '') AS display_name,
               coalesce(n.aliases, []) AS aliases
        ORDER BY label, canonical_name
        """,
        labels=list(EMBED_LABELS),
    )
    return [
        EntityRecord(
            element_id=r["eid"], label=r["label"],
            canonical_name=r["canonical_name"], display_name=r["display_name"],
            aliases=list(r["aliases"]),
        )
        for r in rows
    ]


def fetch_taxons() -> list[EntityRecord]:
    """Taxon nodes with common names aggregated from descendant species."""
    taxon_rows = read_query(
        "MATCH (t:Taxon) RETURN elementId(t) AS eid, t.name AS name, t.rank AS rank "
        "ORDER BY t.rank, t.name"
    )
    alias_rows = read_query(
        """
        MATCH (s)-[:BELONGS_TO*]->(t:Taxon)
        WHERE (s:AnimalSpecies OR s:PlantSpecies) AND NOT s:GenericLocation
        RETURN elementId(t) AS taxon_eid, coalesce(s.aliases, []) AS aliases
        """
    )
    alias_map: dict[str, set[str]] = defaultdict(set)
    for row in alias_rows:
        for alias in row["aliases"]:
            alias = alias.strip()
            if alias and len(alias) > 1:
                alias_map[row["taxon_eid"]].add(alias)
    return [
        EntityRecord(
            element_id=r["eid"], label="Taxon",
            canonical_name=r["name"], display_name=r["name"],
            aliases=sorted(alias_map.get(r["eid"], set())),
            taxon_rank=r["rank"] or "",
        )
        for r in taxon_rows
    ]


def create_vector_indexes() -> None:
    for label, index_name in LABEL_INDEXES.items():
        query(
            f"""
            CREATE VECTOR INDEX {index_name} IF NOT EXISTS
            FOR (n:{label}) ON (n.embedding)
            OPTIONS {{ indexConfig: {{
                `vector.dimensions`: {EMBEDDING_DIM},
                `vector.similarity_function`: 'cosine'
            }} }}
            """
        )
        print(f"  {index_name} ready.", flush=True)


def write_batch(batch: list[EntityRecord]) -> None:
    query(
        """
        UNWIND $rows AS row
        MATCH (n) WHERE elementId(n) = row.eid
        SET n.embeddingDescription = row.description,
            n.embedding = row.embedding,
            n:KGEntity
        """,
        rows=[{"eid": r.element_id, "description": r.description,
               "embedding": r.embedding} for r in batch],
    )


def main() -> None:
    driver().verify_connectivity()
    print(f"Connected; database = {settings().neo4j_database}", flush=True)

    if a.reindex_only:
        create_vector_indexes()
        return

    records = fetch_entities()
    taxons = fetch_taxons()
    all_records = records + taxons
    for rec in all_records:
        rec.description = (build_taxon_description(rec) if rec.label == "Taxon"
                           else build_description(rec))

    counts: dict[str, int] = defaultdict(int)
    for rec in all_records:
        counts[rec.label] += 1
    for label in sorted(counts):
        print(f"  {label}: {counts[label]}", flush=True)
    print(f"  Total: {len(all_records)}", flush=True)

    if a.dry_run:
        import random
        random.seed(2026)  # same samples every run, so dry runs are comparable
        print("\n── Samples ──", flush=True)
        for pool in (records, taxons):
            for rec in sorted(random.sample(pool, min(8, len(pool))),
                              key=lambda r: r.label):
                print(f"\n[{rec.label}] {rec.canonical_name}", flush=True)
                print(f"  {rec.description}", flush=True)
        print("\nDRY RUN — nothing embedded, nothing written.", flush=True)
        return

    from openai import OpenAI
    client = OpenAI(api_key=settings().openai_api_key)
    model = settings().embedding_model
    print(f"\nEmbedding {len(all_records)} descriptions with {model} ...", flush=True)
    t0 = time.time()
    for i in range(0, len(all_records), EMBED_BATCH_SIZE):
        batch = all_records[i:i + EMBED_BATCH_SIZE]
        resp = client.embeddings.create(model=model,
                                        input=[r.description for r in batch])
        for rec, item in zip(batch, resp.data):
            rec.embedding = item.embedding
        print(f"  {min(i + EMBED_BATCH_SIZE, len(all_records))}/{len(all_records)}",
              flush=True)
    print(f"  done in {time.time() - t0:.1f}s", flush=True)

    for i in range(0, len(all_records), WRITE_BATCH_SIZE):
        write_batch(all_records[i:i + WRITE_BATCH_SIZE])
    print(f"Wrote {len(all_records)} nodes.", flush=True)

    create_vector_indexes()
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
