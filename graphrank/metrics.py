"""Scoring retrieval quality without an LLM in the loop.

The headline metric is **answer-entity recall**: given a question whose answer
is a set of named things, does the retrieved context actually contain them? That
is the property RAG lives or dies on, it is deterministic, it costs nothing to
compute, and it does not care which strategy produced the context.

Two supporting metrics keep the headline honest:

``redundancy``  mean pairwise Jaccard overlap of the entity sets of the
                retrieved chunks. High redundancy means the window is full of
                restatements — recall can look fine while the context wastes
                most of its tokens.
``context_tokens``  rough size of what gets sent to the model, so a strategy
                cannot buy recall simply by shipping more text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .config import query
from .models import RetrievalResult

_WORD = re.compile(r"[^a-z0-9]+")


def _normalize(text: str) -> str:
    return _WORD.sub(" ", text.lower()).strip()


def alias_map(names: list[str]) -> dict[str, list[str]]:
    """Fetch every known surface form for a list of canonical entity names.

    Recall measured on canonical names alone badly understates every strategy —
    the journals call Sacagawea "Janey" and Drouillard "Drewyer". The graph
    already stores those aliases, so the metric uses them.
    """
    if not names:
        return {}
    rows = query(
        """
        MATCH (n) WHERE coalesce(n.canonicalName, n.name) IN $names
        RETURN coalesce(n.canonicalName, n.name) AS name,
               coalesce(n.aliases, []) AS aliases
        """,
        names=names,
    )
    resolved = {row["name"]: [row["name"], *row["aliases"]] for row in rows}
    for name in names:
        resolved.setdefault(name, [name])
    return resolved


@dataclass
class Scorecard:
    strategy: str
    question: str
    recall: float = 0.0
    found: list[str] = field(default_factory=list)
    missed: list[str] = field(default_factory=list)
    redundancy: float = 0.0
    context_tokens: int = 0
    elapsed_ms: float = 0.0
    chunk_count: int = 0
    #: Chunks that plain vector top-k would not have returned
    promoted: list[str] = field(default_factory=list)


def entity_recall(
    result: RetrievalResult,
    gold: list[str],
    aliases: dict[str, list[str]] | None = None,
) -> tuple[float, list[str], list[str]]:
    """Fraction of gold answer entities whose name or alias appears in context."""
    if not gold:
        return 0.0, [], []

    aliases = aliases or alias_map(gold)
    haystack = _normalize(result.context_text())

    found, missed = [], []
    for name in gold:
        surface_forms = aliases.get(name, [name])
        if any(_normalize(form) in haystack for form in surface_forms if form):
            found.append(name)
        else:
            missed.append(name)

    return len(found) / len(gold), found, missed


def redundancy(result: RetrievalResult) -> float:
    """Mean pairwise Jaccard overlap of per-chunk entity sets. Lower is better."""
    sets = [
        {e.key() for e in chunk.entities}
        for chunk in result.chunks
        if chunk.entities
    ]
    if len(sets) < 2:
        return 0.0

    scores = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            union = sets[i] | sets[j]
            if union:
                scores.append(len(sets[i] & sets[j]) / len(union))
    return sum(scores) / len(scores) if scores else 0.0


def approx_tokens(text: str) -> int:
    """Cheap token estimate — good enough to compare context sizes."""
    return max(1, len(text) // 4)


def score(
    result: RetrievalResult,
    gold: list[str],
    aliases: dict[str, list[str]] | None = None,
) -> Scorecard:
    recall, found, missed = entity_recall(result, gold, aliases)
    return Scorecard(
        strategy=result.strategy,
        question=result.question,
        recall=recall,
        found=found,
        missed=missed,
        redundancy=redundancy(result),
        context_tokens=approx_tokens(result.context_text()),
        elapsed_ms=result.elapsed_ms,
        chunk_count=len(result.chunks),
        promoted=list(result.debug.get("promoted", [])),
    )
