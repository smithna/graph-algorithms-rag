"""Abort the pipeline if disambiguation has produced mega-clusters."""
import os, sys
sys.path.insert(0, "/Users/nathansmith/Documents/kcdc-2026/graph-algorithms-rag")
os.environ["NEO4J_DATABASE"] = "lewisclark"
from graphrank.config import read_query
r = read_query("""CALL { MATCH (p:Person) RETURN count(p) AS persons }
CALL { MATCH (n) WHERE NOT n:Chunk AND n.aliases IS NOT NULL RETURN max(size(n.aliases)) AS worst }
CALL { MATCH (n) WHERE NOT n:Chunk AND n.aliases IS NOT NULL
       RETURN count(CASE WHEN size(n.aliases) > 120 THEN 1 END) AS mega }
RETURN persons, worst, mega""")[0]
saca = read_query("""MATCH (p:Person {canonicalName:'SACAGAWEA'})
RETURN [a IN coalesce(p.aliases,[]) WHERE toLower(a) CONTAINS 'drewyer'
        OR toLower(a) CONTAINS 'drouillard' OR toLower(a) CONTAINS 'windsor'] AS canary,
       size(coalesce(p.aliases,[])) AS n""")
print(f"GATE: persons={r['persons']} worstCluster={r['worst']} megaClusters={r['mega']}")
fail = []
if r["mega"] > 0:            fail.append(f"{r['mega']} cluster(s) with >120 aliases")
if r["worst"] > 200:         fail.append(f"worst cluster {r['worst']} aliases")
if r["persons"] < 650:       fail.append(f"Person count collapsed to {r['persons']}")
if saca and saca[0]["canary"]:
    fail.append(f"CANARY: Drouillard/Windsor merged into SACAGAWEA -> {saca[0]['canary'][:4]}")
if saca: print(f"GATE: SACAGAWEA aliases={saca[0]['n']}")
if fail:
    print("GATE FAILED: " + "; ".join(fail)); sys.exit(1)
print("GATE PASSED")
