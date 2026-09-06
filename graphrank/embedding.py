"""Question embedding with an on-disk cache.

The corpus is already embedded in the graph. The only thing this repo ever
sends to OpenAI is the user's question — and it caches those so a benchmark
run costs nothing after the first pass and stays byte-for-byte repeatable.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from .config import settings

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "embeddings"


def _cache_path(text: str, model: str) -> Path:
    key = hashlib.sha256(f"{model}::{text}".encode()).hexdigest()[:32]
    return CACHE_DIR / f"{key}.json"


@lru_cache(maxsize=1)
def _client():
    from openai import OpenAI

    return OpenAI(api_key=settings().openai_api_key)


def embed(text: str, *, use_cache: bool = True) -> list[float]:
    """Embed a single string, caching the result on disk."""
    model = settings().embedding_model
    path = _cache_path(text, model)

    if use_cache and path.exists():
        return json.loads(path.read_text())

    response = _client().embeddings.create(model=model, input=text)
    vector = response.data[0].embedding

    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(vector))

    return vector
