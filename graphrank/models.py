"""Shared result types.

Every retrieval strategy returns the same shape so the benchmark harness can
compare them without knowing how they work.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Entity:
    label: str
    name: str
    community_id: int | None = None

    def key(self) -> str:
        return f"{self.label}:{self.name}"


@dataclass
class Relationship:
    from_name: str
    from_type: str
    rel_type: str
    to_name: str
    to_type: str
    chunk_id: str | None = None
    date: str | None = None

    def describe(self) -> str:
        return (
            f"{self.from_name} ({self.from_type}) "
            f"-[{self.rel_type}]-> {self.to_name} ({self.to_type})"
        )


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    date: str | None = None
    author: str | None = None
    #: Cosine similarity from the chunk vector index, if the chunk came from it
    vector_score: float | None = None
    #: Algorithm score (personalized PageRank, path evidence weight, ...)
    graph_score: float | None = None
    #: Score the strategy actually ranked on
    final_score: float = 0.0
    #: How this chunk entered the result set
    source: str = "vector"
    entities: list[Entity] = field(default_factory=list)
    community_id: int | None = None


@dataclass
class Path:
    """One explanatory route between two anchor concepts."""

    nodes: list[Entity]
    relationships: list[Relationship]
    total_cost: float = 0.0

    def describe(self) -> str:
        if not self.relationships:
            return " / ".join(n.name for n in self.nodes)
        parts = [self.nodes[0].name]
        for rel, node in zip(self.relationships, self.nodes[1:]):
            parts.append(f"-[{rel.rel_type}]->")
            parts.append(node.name)
        return " ".join(parts)

    @property
    def hops(self) -> int:
        return len(self.relationships)

    def chunk_ids(self) -> list[str]:
        return [r.chunk_id for r in self.relationships if r.chunk_id]


@dataclass
class RetrievalResult:
    question: str
    strategy: str
    chunks: list[RetrievedChunk] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    paths: list[Path] = field(default_factory=list)
    elapsed_ms: float = 0.0
    #: Strategy-specific diagnostics — seed chunks, community ids, anchors, ...
    debug: dict[str, Any] = field(default_factory=dict)

    def chunk_ids(self) -> list[str]:
        return [c.chunk_id for c in self.chunks]

    def context_text(self) -> str:
        """Everything this strategy would hand to the LLM, as one string."""
        blocks: list[str] = []
        for i, chunk in enumerate(self.chunks, 1):
            header = " · ".join(x for x in (chunk.author, chunk.date) if x)
            blocks.append(f"[Passage {i}{f' — {header}' if header else ''}]\n{chunk.text}")
        body = "\n\n---\n\n".join(blocks)

        if self.paths:
            body += "\n\n=== CONNECTING PATHS ===\n" + "\n".join(
                p.describe() for p in self.paths
            )
        if self.relationships:
            body += "\n\n=== GRAPH RELATIONSHIPS ===\n" + "\n".join(
                r.describe() for r in self.relationships
            )
        return body
