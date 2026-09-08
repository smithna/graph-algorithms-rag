"""Scoring retrieval quality without an LLM in the loop.

The headline metric is **answer-entity recall**: given a question whose answer
is a set of named things, does the retrieved context actually contain them? That
is the property RAG lives or dies on, it is deterministic, it costs nothing to
compute, and it does not care which strategy produced the context.

A gold entity is a :class:`GoldTarget` — a display name pinned to one
``(canonicalName, label)`` node, verified by ``scripts/verify_questions.py``.
It counts as *found* when either

1. the pinned node has a ``MENTIONED_IN`` edge into a retrieved chunk — the
   extraction pipeline's own judgement that the passage is about the entity,
   which is what catches the spellings the alias list never recorded
   ("buffaloe", "quawmash") and coreference ("we proceeded on" resolved to a
   captain); or
2. any surface form the graph knows for the node appears in a retrieved
   passage's text — on token boundaries, and not merely as the inside of a
   longer surface form belonging to a *different* node ("GREAT FALLS" occurring
   only inside "great falls of the Columbia" is the wrong falls; "MANDAN"
   inside "Fort Mandan" is a building, not the nation — both were live false
   credits before this rule).

Both checks are deterministic. The text check deliberately reads **passage
text only**, not the full prompt payload: the GRAPH RELATIONSHIPS block that
``context_text()`` appends is an unordered LIMIT-slice, and letting it satisfy
recall would score a decoration lottery rather than the retrieval decision.

Two supporting metrics keep the headline honest:

``redundancy``  mean pairwise Jaccard overlap of the entity sets of the
                retrieved chunks. High redundancy means the window is full of
                restatements — recall can look fine while the context wastes
                most of its tokens.
``context_tokens``  rough size of what gets sent to the model (the full
                payload, relationships included), so a strategy cannot buy
                recall simply by shipping more text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

from .config import query
from .models import RetrievalResult

_WORD = re.compile(r"[^a-z0-9]+")


def _normalize(text: str) -> str:
    return _WORD.sub(" ", text.lower()).strip()


def _spans(haystack: str, needle: str) -> list[tuple[int, int]]:
    """Token-boundary occurrences of ``needle`` in a normalized haystack."""
    padded = f" {haystack} "
    target = f" {needle} "
    spans, start = [], 0
    while True:
        i = padded.find(target, start)
        if i < 0:
            return spans
        spans.append((i, i + len(needle) + 2))
        start = i + 1


@lru_cache(maxsize=1)
def _all_surface_strings() -> frozenset[str]:
    """Every normalized name and alias in the graph, for shadow detection."""
    rows = query(
        """
        MATCH (n) WHERE NOT n:Chunk
        RETURN coalesce(n.canonicalName, n.name) AS name,
               coalesce(n.aliases, []) AS aliases
        """
    )
    out = set()
    for row in rows:
        for s in [row["name"], *row["aliases"]]:
            if s:
                out.add(_normalize(s))
    return frozenset(out)


@lru_cache(maxsize=4096)
def _shadows(form: str, own_forms: frozenset[str]) -> tuple[str, ...]:
    """Longer surface forms of OTHER nodes that contain this form.

    "GREAT FALLS" appearing only inside "great falls of the Columbia" is the
    wrong falls; "MANDAN" inside "Fort Mandan" is a building, not the nation.
    A text match that is entirely covered by such a longer form earns nothing.
    """
    return tuple(
        s
        for s in _all_surface_strings()
        if s not in own_forms and len(s) > len(form) and _spans(s, form)
    )


def _text_match(haystack: str, form: str, shadows: tuple[str, ...]) -> bool:
    """True if ``form`` occurs at least once OUTSIDE every shadowing span."""
    occurrences = _spans(haystack, form)
    if not occurrences:
        return False
    if not shadows:
        return True
    covered: list[tuple[int, int]] = []
    for shadow in shadows:
        covered.extend(_spans(haystack, shadow))
    return any(
        not any(cs <= s and e <= ce for cs, ce in covered)
        for s, e in occurrences
    )


@dataclass(frozen=True)
class GoldTarget:
    """One gold entity: a display name pinned to a specific node."""

    concept: str  # display name from questions.yaml `gold`
    name: str  # canonicalName of the pinned node
    label: str  # node label — a bare name cannot address the right node


def gold_targets(entry: dict) -> list[GoldTarget]:
    """Build the target list for one question-bank entry.

    Every `gold` display name must have a `targets` pin; anything else is a
    hard error because an unpinned name is exactly how the old benchmark
    scored decoy nodes without noticing.
    """
    gold = entry.get("gold", []) or []
    pins = entry.get("targets", {}) or {}
    targets = []
    for concept in gold:
        pin = pins.get(concept)
        if not pin or len(pin) != 2:
            raise ValueError(
                f"{entry.get('id', '?')}: gold entry '{concept}' has no "
                f"[canonicalName, label] pin under targets: — run "
                f"scripts/verify_questions.py"
            )
        targets.append(GoldTarget(concept=concept, name=pin[0], label=pin[1]))
    return targets


def surface_forms(targets: list[GoldTarget]) -> dict[str, list[str]]:
    """Every known surface form per gold concept, from the pinned node.

    Recall measured on canonical names alone badly understates every strategy —
    the journals call Sacagawea "Janey" and the elk lives on a node named
    CERVUS CANADENSIS. The graph already stores the aliases, so the metric uses
    them, plus the display name itself.
    """
    if not targets:
        return {}
    rows = query(
        """
        UNWIND $targets AS t
        MATCH (n) WHERE coalesce(n.canonicalName, n.name) = t.name
          AND t.label IN labels(n) AND NOT n:Chunk
        RETURN t.concept AS concept,
               coalesce(n.canonicalName, n.name) AS name,
               coalesce(n.aliases, []) AS aliases
        """,
        targets=[t.__dict__ for t in targets],
    )
    forms = {
        row["concept"]: [row["concept"], row["name"], *row["aliases"]]
        for row in rows
    }
    for t in targets:
        forms.setdefault(t.concept, [t.concept, t.name])
    return forms


def mentioned_concepts(chunk_ids: list[str], targets: list[GoldTarget]) -> set[str]:
    """Concepts whose pinned node has a mention edge into the retrieved set."""
    if not chunk_ids or not targets:
        return set()
    rows = query(
        """
        UNWIND $targets AS t
        MATCH (n) WHERE coalesce(n.canonicalName, n.name) = t.name
          AND t.label IN labels(n) AND NOT n:Chunk
        MATCH (n)-[:MENTIONED_IN]->(c:Chunk) WHERE c.chunkId IN $chunkIds
        RETURN DISTINCT t.concept AS concept
        """,
        targets=[t.__dict__ for t in targets],
        chunkIds=chunk_ids,
    )
    return {row["concept"] for row in rows}


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
    #: Question-bank id and kind, for per-kind reporting
    question_id: str = ""
    kind: str = ""


def entity_recall(
    result: RetrievalResult,
    targets: list[GoldTarget],
    forms: dict[str, list[str]] | None = None,
) -> tuple[float, list[str], list[str]]:
    """Fraction of gold targets present in the retrieved passages."""
    if not targets:
        return 0.0, [], []

    forms = forms or surface_forms(targets)
    by_mention = mentioned_concepts(result.chunk_ids(), targets)
    haystack = _normalize("\n".join(chunk.text for chunk in result.chunks))

    found, missed = [], []
    for t in targets:
        own = frozenset(
            _normalize(f) for f in forms.get(t.concept, []) if f
        )
        if t.concept in by_mention or any(
            _text_match(haystack, form, _shadows(form, own)) for form in own
        ):
            found.append(t.concept)
        else:
            missed.append(t.concept)

    return len(found) / len(targets), found, missed


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
    targets: list[GoldTarget],
    forms: dict[str, list[str]] | None = None,
) -> Scorecard:
    recall, found, missed = entity_recall(result, targets, forms)
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
