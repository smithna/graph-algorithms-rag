#!/usr/bin/env python3
"""Verify the environment before anything else runs.

Checks the connection, the GDS plugin, the graph's shape, and every index this
repo depends on. Run it first — it turns three confusing failures later into
one clear message now.
"""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from rich.console import Console
from rich.table import Table

from graphrank.config import gds, query, settings

console = Console()

REQUIRED_VECTOR_INDEXES = [
    "chunk_embeddings",
    "person_embeddings",
    "place_embeddings",
    "waterbody_embeddings",
    "animalspecies_embeddings",
    "plantspecies_embeddings",
    "nativenation_embeddings",
    "event_embeddings",
    "taxon_embeddings",
]
REQUIRED_FULLTEXT_INDEXES = ["person_search", "location_search", "native_nation_search"]


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()

    cfg = settings()
    console.rule("[bold]Environment")
    console.print(f"URI       {cfg.neo4j_uri}")
    console.print(f"Database  {cfg.neo4j_database}")
    console.print(f"Graph     {cfg.graph_name}")

    failures: list[str] = []

    # ── Connection ───────────────────────────────────────────────────────────
    try:
        query("RETURN 1 AS ok")
        console.print("[green]✓[/] connected to Neo4j")
    except Exception as exc:
        console.print(f"[red]✗[/] cannot connect: {exc}")
        return 1

    # ── GDS ──────────────────────────────────────────────────────────────────
    try:
        version = gds().version()
        console.print(f"[green]✓[/] GDS plugin {version}")
    except Exception as exc:
        console.print(f"[red]✗[/] GDS unavailable: {exc}")
        failures.append("GDS plugin is required for PageRank, Louvain, and Yen's")

    # ── Graph shape ──────────────────────────────────────────────────────────
    counts = query(
        """
        CALL {  MATCH (c:Chunk) RETURN count(c) AS chunks }
        CALL { MATCH (e) WHERE NOT e:Chunk AND e.canonicalName IS NOT NULL
               RETURN count(e) AS entities }
        CALL { MATCH ()-[r:MENTIONED_IN]->() RETURN count(r) AS mentions }
        CALL { MATCH ()-[r:NEXT_CHUNK]->() RETURN count(r) AS sequence }
        RETURN chunks, entities, mentions, sequence
        """
    )[0]

    table = Table(show_header=True, header_style="bold")
    table.add_column("Element")
    table.add_column("Count", justify="right")
    for key, label in [
        ("chunks", "Chunk nodes"),
        ("entities", "Entity nodes"),
        ("mentions", "MENTIONED_IN"),
        ("sequence", "NEXT_CHUNK"),
    ]:
        table.add_row(label, f"{counts[key]:,}")
    console.print(table)

    if counts["chunks"] == 0:
        failures.append("No Chunk nodes — restore the corps-of-discovery dump first")
    if counts["mentions"] == 0:
        failures.append("No MENTIONED_IN relationships — the entity layer is missing")

    # ── Indexes ──────────────────────────────────────────────────────────────
    existing = {
        row["name"]: row["type"]
        for row in query("SHOW INDEXES YIELD name, type RETURN name, type")
    }

    missing_vector = [i for i in REQUIRED_VECTOR_INDEXES if i not in existing]
    missing_fulltext = [i for i in REQUIRED_FULLTEXT_INDEXES if i not in existing]

    if missing_vector:
        console.print(f"[yellow]![/] missing vector indexes: {', '.join(missing_vector)}")
        if "chunk_embeddings" in missing_vector:
            failures.append("chunk_embeddings is required — nothing works without it")
    else:
        console.print("[green]✓[/] all vector indexes present")

    if missing_fulltext:
        console.print(
            f"[yellow]![/] missing full-text indexes: {', '.join(missing_fulltext)} "
            "(anchor resolution falls back to vector search)"
        )
    else:
        console.print("[green]✓[/] all full-text indexes present")

    console.rule()
    if failures:
        for failure in failures:
            console.print(f"[red]✗ {failure}[/]")
        return 1

    console.print("[bold green]Ready.[/] Next: python scripts/project_graph.py")
    return 0


if __name__ == "__main__":
    from graphrank.cli import run

    raise SystemExit(run(main))
