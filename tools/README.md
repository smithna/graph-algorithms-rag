# tools/

Not part of the retrieval/algorithms story in `graphrank/` — this is what it
took to get the shared Lewis & Clark graph (built by
[corps-of-discovery-graph-rag](https://github.com/smithna/corps-of-discovery-graph-rag))
into a state the algorithms could run against honestly, before `graphrank/`
ever touched it. **This is re-extraction and re-resolution, not just
retrieval** — worth saying plainly, since the top-level README's "no
re-ingest" line is easy to over-read as "nothing about the corpus changed."
The raw text was never re-chunked or re-loaded, and chunk embeddings are
untouched, but entity resolution and taxonomy assignment *were* rerun end to
end against a newer model (`gpt-5.6-luna`, replacing `gpt-4o-mini`) once
measurement showed the original pass had real gaps. They're here for
provenance, not for you to run against your own graph.

| file | what it did |
|---|---|
| `disambiguate_layered.py` | Layered entity-resolution merge: candidates → adjudicate → evidence → transitivity → consistency → merge. Read-only until `--apply`; the merge is gated. |
| `gate.py` | Sanity check run after disambiguation — aborts if it produced mega-clusters or merged entities that shouldn't be merged (the Sacagawea/Drouillard/Windsor canary). |
| `embed_entities.py` | New embeddings for the four label types that get vector-searched (`AnimalSpecies`, `PlantSpecies`, `Event`, `Taxon`) — needed because taxonomy re-extraction replaced their names with Latin binomials that share no vocabulary with how people actually ask ("grizzly bear" vs `URSUS ARCTOS HORRIBILIS`). The rest stay full-text-only by design. |
| `resolve_species_names.py` | Species-name resolution and taxonomy repair against the corpus's common names. |
| `audit_taxonomy.py` | Regression check for the taxonomy repair above. |
| `corps-patches/*.patch` | Patches against specific `corps-of-discovery-graph-rag` scripts (`add_taxonomy.py`, `disambiguate.py`, `resolve_mentions.py`, `enrich_sacagawea.py`, `tag_corps_members.py`, `setup_fulltext_indexes.py`), applied there. The three that touch an LLM bump `RESOLUTION_MODEL`/`EXTRACTION_MODEL` from `gpt-4o-mini` to `gpt-5.6-luna` — that's the re-extraction and re-resolution referenced above. See each patch's own diff header for which file it targets. |

If you're setting up your own corpus from scratch, you likely don't need any
of this — start from `corps-of-discovery-graph-rag` directly and skip
straight to this repo's own `README.md` for the retrieval/algorithms layer.
