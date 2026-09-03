"""
z3 spot-check of the no-new-mono + L3 constraints over the 24 canonical
classes (produces the artifacts for the claimed "z3 UNSAT on all
spot-checked classes" independent confirmation).

Uses the z3 encoding from computation/gen_search.z3_l3_feasible verbatim
(imported), but runs it over ALL 24 cached classes with bounded timeouts
and records sat/unsat/unknown per class.
"""
import pickle, sys, time
sys.path.insert(0, "/Users/junhaoliang/Projects/Krenn-Gu/computation")
from gen_search import z3_l3_feasible   # their encoder; we run the matrix

with open("/Users/junhaoliang/Projects/Krenn-Gu/computation/triples_cache.pkl", "rb") as f:
    reps = pickle.load(f)

results = []
t0 = time.time()
for idx, (P0, P1, P2) in enumerate(reps):
    t1 = time.time()
    try:
        res, _model = z3_l3_feasible(P0, P1, P2)
        dt = time.time() - t1
    except Exception as ex:
        res, dt = "ERROR:" + str(ex), time.time() - t1
    results.append((idx, (len(P0), len(P1), len(P2)), res, dt))
    print(f"class {idx:2d} size={len(P0),len(P1),len(P2)} -> {res} ({dt:.0f}s)", flush=True)
    if res == "SAT":
        print("*** SAT FOUND *** — would refute the batch claim; aborting", flush=True)
        sys.exit(2)
    if time.time() - t0 > 2400:   # hard budget 40 min
        print("budget exhausted; remaining classes UNKNOWN", flush=True)
        break

from collections import Counter
print("summary:", Counter(r[2] for r in results))
with open("z3_spotcheck_results.json", "w") as f:
    import json
    json.dump([{"idx": r[0], "size": r[1], "verdict": r[2], "secs": r[3]} for r in results], f, indent=2)
print("results written to z3_spotcheck_results.json")
