"""Graph algorithms for RAG context retrieval and ranking.

Vector similarity gets you candidates. Graph algorithms decide which of those
candidates actually answer the question.

This package layers three algorithm-driven retrieval strategies on top of the
Lewis & Clark knowledge graph built by ``corps-of-discovery-graph-rag``:

* :mod:`graphrank.pagerank`    — personalized PageRank reranking
* :mod:`graphrank.communities` — Louvain community detection
* :mod:`graphrank.paths`       — Yen's k-shortest-path exploration
"""

__version__ = "0.1.0"
