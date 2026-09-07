"""How much of the mention graph is rented from build-time coreference?

Finding 5g said filter+cosine parity is "rented from build-time coreference":
the tag filter only sees the Nov-4 passage because ``extract.py`` resolved
"one of his wives" -> SACAGAWEA when the graph was built. This script sizes
the rent, on mass, with no relevance proxy — pure set membership between a
chunk's text and the entity's known surface forms.

Every ``MENTIONED_IN`` edge is classified by what textual support it has in
the chunk, whitespace-normalized and case-folded:

``name-backed``   the chunk contains the canonical name or a *name-like*
                  alias (shares a content token with the canonical name, or
                  is string-similar to it — the misspelling case). A plain
                  NER tagger with a name gazetteer would produce this edge.
``surface-only``  the chunk contains only a *descriptive* alias ("the squaw",
                  "the interpreter's wife", "This River"). The string is in
                  the text, but linking it to the entity already required
                  coreference at build time — the alias list itself is a
                  coreference artifact.
``inference``     no known surface form appears in the chunk at all. The
                  edge exists purely because extraction resolved a pronoun
                  or an implicit reference. No tag filter has this edge on
                  an ordinary-extraction corpus, at any gazetteer size.

Two honest caveats, stated up front:

- The name-like classifier is a heuristic, so the name-backed/surface-only
  boundary is approximate. The ``inference`` class is classifier-free —
  containment of *any* known form — and is the number to quote. It is still
  contaminated in both directions: gazetteer gaps inflate it (a 1805-07-26
  chunk says "shabono", but only "Toust. Shabono" is filed as an alias, so
  containment misses — that edge is a recording gap, not coreference), and
  the surface-only class deflates it (linking "the squaw" to SACAGAWEA was
  itself build-time coreference). Treat 12% as a size class, not a constant;
  the per-passage receipts are what the hand reads verify.
- ``add_taxonomy.py`` renamed species to Latin binomials, so species read as
  massively coref-only under name-matching ("deer" is not name-like for
  ODOCOILEUS VIRGINIANUS). That is arguably faithful to what strict NER
  gives you (it does not tag common nouns at all), but quote the
  proper-noun labels (Person, NativeNation, Place, WaterBody) when the
  claim is about coreference rather than about vocabulary normalization.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "scripts")
import _bootstrap  # noqa: F401

from graphrank.config import query

#: Tokens that never make an alias name-like on their own — determiners,
#: kinship and role words, and the generic geographic/ethnographic nouns this
#: corpus leans on.
STOPWORDS = {
    "the", "of", "a", "an", "his", "her", "their", "this", "that", "one",
    "some", "and", "or", "to", "in", "on", "at", "with", "river", "creek",
    "man", "men", "wife", "wives", "party", "people", "nation", "indians",
    "indian", "chief", "old", "big", "little", "great", "white", "black",
}


def normalize(s: str) -> str:
    """Case-fold and collapse whitespace — chunk text is hard-wrapped, and an
    alias spanning a line break must still count as present."""
    return re.sub(r"\s+", " ", s.lower())


def content_tokens(s: str) -> set[str]:
    return {
        t for t in re.findall(r"[a-z]+", s.lower())
        if len(t) > 2 and t not in STOPWORDS
    }


def jaro_winkler(s1: str, s2: str) -> float:
    s1, s2 = s1.lower(), s2.lower()
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if not len1 or not len2:
        return 0.0
    window = max(len1, len2) // 2 - 1
    hit1 = [False] * len1
    hit2 = [False] * len2
    matches = 0
    for i, ch in enumerate(s1):
        lo, hi = max(0, i - window), min(len2, i + window + 1)
        for j in range(lo, hi):
            if not hit2[j] and s2[j] == ch:
                hit1[i] = hit2[j] = True
                matches += 1
                break
    if not matches:
        return 0.0
    transpositions = 0
    k = 0
    for i in range(len1):
        if hit1[i]:
            while not hit2[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1
    transpositions //= 2
    jaro = (
        matches / len1 + matches / len2 + (matches - transpositions) / matches
    ) / 3
    prefix = 0
    for a, b in zip(s1, s2):
        if a == b and prefix < 4:
            prefix += 1
        else:
            break
    return jaro + 0.1 * prefix * (1 - jaro)


def name_like(alias: str, canonical: str) -> bool:
    """A name-like alias shares a content token with the canonical name or is
    string-similar to it (the Sahcahgarweah case). Everything else is a
    description that only coreference could have linked."""
    a_toks = content_tokens(alias)
    c_toks = content_tokens(canonical)
    if a_toks & c_toks:
        return True
    if jaro_winkler(alias, canonical) >= 0.80:
        return True
    return any(jaro_winkler(a, c) >= 0.84 for a in a_toks for c in c_toks)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--entity",
        action="append",
        default=[],
        help="canonical name; list that entity's inference edges in full",
    )
    args = parser.parse_args()

    chunks = {
        row["id"]: {
            "text": normalize(row["text"]),
            "date": row["date"],
            "chunkId": row["chunkId"],
        }
        for row in query(
            "MATCH (c:Chunk) RETURN id(c) AS id, c.text AS text, "
            "toString(c.date) AS date, c.chunkId AS chunkId"
        )
    }

    entities = query(
        """
        MATCH (e)-[:MENTIONED_IN]->(:Chunk)
        WHERE NOT e:Chunk AND NOT e:GenericLocation
        WITH DISTINCT e
        RETURN id(e) AS id, head(labels(e)) AS label,
               coalesce(e.canonicalName, e.name) AS canonical,
               coalesce(e.aliases, []) AS aliases
        """
    )
    name_forms: dict[int, list[str]] = {}
    all_forms: dict[int, list[str]] = {}
    meta: dict[int, tuple[str, str]] = {}
    for e in entities:
        canonical = e["canonical"] or ""
        names = {normalize(canonical)} if canonical else set()
        everything = set(names)
        for alias in e["aliases"]:
            form = normalize(alias)
            everything.add(form)
            if name_like(alias, canonical):
                names.add(form)
        name_forms[e["id"]] = sorted(names)
        all_forms[e["id"]] = sorted(everything)
        meta[e["id"]] = (e["label"], canonical)

    edges = query(
        """
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
        WHERE NOT e:Chunk AND NOT e:GenericLocation
        RETURN DISTINCT id(e) AS eid, id(c) AS cid
        """
    )

    classes: dict[str, list[dict]] = defaultdict(list)
    for edge in edges:
        text = chunks[edge["cid"]]["text"]
        if any(f in text for f in name_forms[edge["eid"]]):
            classes["name-backed"].append(edge)
        elif any(f in text for f in all_forms[edge["eid"]]):
            classes["surface-only"].append(edge)
        else:
            classes["inference"].append(edge)

    total = len(edges)
    print(f"{total} MENTIONED_IN edges, {len(entities)} entities\n")
    for cls in ("name-backed", "surface-only", "inference"):
        n = len(classes[cls])
        print(f"  {cls:12s} {n:6d}  ({100 * n / total:.1f}%)")

    print("\ninference share by label (classifier-free — the quotable number):")
    inf_by_label = Counter(meta[e["eid"]][0] for e in classes["inference"])
    all_by_label = Counter(meta[e["eid"]][0] for e in edges)
    for label, n_all in all_by_label.most_common():
        n = inf_by_label.get(label, 0)
        print(f"  {label:14s} {n:5d} / {n_all:5d}  ({100 * n / n_all:.1f}%)")

    print("\ntop entities by inference edges:")
    by_entity = Counter(meta[e["eid"]] for e in classes["inference"])
    for (label, canonical), n in by_entity.most_common(12):
        print(f"  {n:4d}  {label:14s} {canonical}")

    for wanted in args.entity:
        print(f"\n--- inference edges for {wanted} ---")
        ids = [eid for eid, (_, cn) in meta.items() if cn == wanted]
        if not ids:
            print("  (no such entity)")
            continue
        for edge in classes["inference"]:
            if edge["eid"] in ids:
                chunk = chunks[edge["cid"]]
                print(
                    f"  {chunk['date']}  {chunk['chunkId']}  "
                    f"{chunk['text'][:90]!r}"
                )


if __name__ == "__main__":
    main()
