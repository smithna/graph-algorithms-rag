# tools/

One-time corpus-preparation utilities, not part of the retrieval/algorithms
story in `graphrank/`. This repo's own line is "no re-ingest, no
re-extraction, no re-embedding" — these are the scripts that got the shared
Lewis & Clark graph (built by
[corps-of-discovery-graph-rag](https://github.com/smithna/corps-of-discovery-graph-rag))
into a state where that promise could be kept, before the algorithms in
`graphrank/` ever touched it. They're here for provenance, not for you to run
against your own graph.

| file | what it did |
|---|---|
| `disambiguate_layered.py` | Layered entity-resolution merge: candidates → adjudicate → evidence → transitivity → consistency → merge. Read-only until `--apply`; the merge is gated. |
| `gate.py` | Sanity check run after disambiguation — aborts if it produced mega-clusters or merged entities that shouldn't be merged (the Sacagawea/Drouillard/Windsor canary). |
| `embed_entities.py` | One-time embeddings for the four label types that get vector-searched (`AnimalSpecies`, `PlantSpecies`, `Event`, `Taxon`) — the rest stay full-text-only by design. |
| `resolve_species_names.py` | Species-name resolution and taxonomy repair against the corpus's common names. |
| `audit_taxonomy.py` | Regression check for the taxonomy repair above. |
| `corps-patches/*.patch` | Patches against specific `corps-of-discovery-graph-rag` scripts, applied there to fix bugs this project's measurements surfaced (see each patch's own diff header for which file it targets). |

If you're setting up your own corpus from scratch, you likely don't need any
of this — start from `corps-of-discovery-graph-rag` directly and skip
straight to this repo's own `README.md` for the retrieval/algorithms layer.
