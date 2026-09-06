"""Settings, driver, and GDS client.

Everything reads from ``.env`` (see ``.env.example``). Connections are lazily
created singletons so scripts can just import and go.
"""

from __future__ import annotations

import atexit
import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    """Raised when a required environment variable is missing."""


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value or value.startswith("your-") or value == "sk-...":
        raise ConfigError(
            f"{name} is not set. Copy .env.example to .env and fill it in."
        )
    return value


@dataclass(frozen=True)
class Settings:
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str
    embedding_model: str
    graph_name: str
    next_chunk_weight: float
    related_weight: float

    @property
    def openai_api_key(self) -> str:
        # Resolved lazily: the projection and algorithm scripts do not need it,
        # only question embedding does.
        return _require("OPENAI_API_KEY")


@lru_cache(maxsize=1)
def settings() -> Settings:
    return Settings(
        neo4j_uri=_require("NEO4J_URI"),
        neo4j_user=_require("NEO4J_USER"),
        neo4j_password=_require("NEO4J_PASSWORD"),
        neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j"),
        embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        graph_name=os.getenv("GRAPH_NAME", "lc-retrieval"),
        next_chunk_weight=float(os.getenv("NEXT_CHUNK_WEIGHT", "1.0")),
        related_weight=float(os.getenv("RELATED_WEIGHT", "1.0")),
    )


@lru_cache(maxsize=1)
def driver():
    """Shared Neo4j driver."""
    from neo4j import GraphDatabase

    cfg = settings()
    return GraphDatabase.driver(
        cfg.neo4j_uri, auth=(cfg.neo4j_user, cfg.neo4j_password)
    )


@lru_cache(maxsize=1)
def gds():
    """Shared GDS client, bound to the configured database."""
    from graphdatascience import GraphDataScience

    cfg = settings()
    client = GraphDataScience(
        cfg.neo4j_uri, auth=(cfg.neo4j_user, cfg.neo4j_password)
    )
    client.set_database(cfg.neo4j_database)
    return client


def query(cypher: str, **params) -> list[dict]:
    """Run a read/write query and return plain dicts."""
    cfg = settings()
    with driver().session(database=cfg.neo4j_database) as session:
        return [record.data() for record in session.run(cypher, **params)]


@atexit.register
def _close() -> None:
    for factory in (driver, gds):
        if factory.cache_info().currsize:
            try:
                factory().close()
            except Exception:  # pragma: no cover - best-effort cleanup
                pass
