"""Resolve natural-language mentions to nodes in the graph.

Proper nouns go through the full-text indexes (token matching beats cosine
similarity on names like "Columbia River"); concepts go through the per-label
vector indexes. Both index families are created by the corps-of-discovery
pipeline — this repo only reads them.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import query
from .embedding import embed

#: Per-label vector indexes created by embed_entities.py
LABEL_VECTOR_INDEX: dict[str, str] = {
    "Person": "person_embeddings",
    "Place": "place_embeddings",
    "WaterBody": "waterbody_embeddings",
    "AnimalSpecies": "animalspecies_embeddings",
    "PlantSpecies": "plantspecies_embeddings",
    "NativeNation": "nativenation_embeddings",
    "Event": "event_embeddings",
    "Taxon": "taxon_embeddings",
}

#: Per-label full-text indexes created by setup_fulltext_indexes.py
LABEL_FULLTEXT_INDEX: dict[str, str] = {
    "Person": "person_search",
    "Place": "location_search",  # covers Place + WaterBody
    "WaterBody": "location_search",
    "NativeNation": "native_nation_search",
}

_LUCENE_SPECIAL = set('+-&|!(){}[]^"~*?:\\/')


@dataclass
class ResolvedEntity:
    label: str
    name: str
    node_id: int
    score: float
    resolved_via: str  # "fulltext" | "vector"


def _escape_lucene(text: str) -> str:
    return "".join(f"\\{c}" if c in _LUCENE_SPECIAL else c for c in text)


def resolve_entity(text: str, label: str | None = None) -> ResolvedEntity | None:
    """Find the single best node for a phrase, optionally constrained to a label."""
    if label:
        hit = _resolve_in_label(text, label)
        return hit

    # No label given: try every full-text index and keep the strongest hit.
    best: ResolvedEntity | None = None
    for candidate_label in ("Person", "Place", "NativeNation"):
        hit = _fulltext_lookup(text, candidate_label)
        if hit and (best is None or hit.score > best.score):
            best = hit
    if best:
        return best

    # Fall back to semantic labels.
    for candidate_label in ("Event", "AnimalSpecies", "PlantSpecies", "Taxon"):
        hit = _vector_lookup(text, candidate_label)
        if hit and (best is None or hit.score > best.score):
            best = hit
    return best


def _resolve_in_label(text: str, label: str) -> ResolvedEntity | None:
    if label in LABEL_FULLTEXT_INDEX:
        hit = _fulltext_lookup(text, label)
        if hit:
            return hit
    return _vector_lookup(text, label)


def _fulltext_lookup(text: str, label: str) -> ResolvedEntity | None:
    index = LABEL_FULLTEXT_INDEX.get(label)
    if not index:
        return None
    rows = query(
        f"""
        CALL db.index.fulltext.queryNodes('{index}', $q)
        YIELD node, score
        WHERE NOT node:GenericLocation
        RETURN coalesce(node.canonicalName, node.name) AS name,
               head(labels(node))                      AS label,
               id(node)                                AS nodeId,
               score
        LIMIT 1
        """,
        q=_escape_lucene(text),
    )
    if not rows or not rows[0]["name"]:
        return None
    row = rows[0]
    return ResolvedEntity(
        label=row["label"],
        name=row["name"],
        node_id=row["nodeId"],
        score=row["score"],
        resolved_via="fulltext",
    )


def _vector_lookup(text: str, label: str) -> ResolvedEntity | None:
    index = LABEL_VECTOR_INDEX.get(label)
    if not index:
        return None
    rows = query(
        f"""
        CALL db.index.vector.queryNodes('{index}', 1, $embedding)
        YIELD node, score
        WHERE NOT node:GenericLocation
        RETURN coalesce(node.canonicalName, node.name) AS name,
               head(labels(node))                      AS label,
               id(node)                                AS nodeId,
               score
        """,
        embedding=embed(text),
    )
    if not rows or not rows[0]["name"]:
        return None
    row = rows[0]
    return ResolvedEntity(
        label=row["label"],
        name=row["name"],
        node_id=row["nodeId"],
        score=row["score"],
        resolved_via="vector",
    )
