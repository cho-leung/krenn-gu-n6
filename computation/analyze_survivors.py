"""Independent analysis of L3-survivors: run decide() and report verdicts."""
import json, collections, sys
import sympy as sp
from search_core import decide, ABSENT
from k6_basics import EDGES

def load(path):
    recs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs

def main(path, max_n=None):
    recs = load(path)
    if max_n:
        recs = recs[:max_n]
    stats = collections.Counter()
    feas = []
    for i, rec in enumerate(recs):
        coloring = {}
        for e in EDGES:
            key = f"{e[0]}{e[1]}"
            v = rec["coloring"].get(key)
            coloring[e] = ABSENT if v is None else tuple(v)
        verdict, info = decide(coloring)
        key = (verdict, info.get("reason", "")[:45])
        stats[key] += 1
        if verdict == "FEASIBLE":
            feas.append((rec, coloring, info))
        if verdict == "UNRESOLVED":
            print(f"UNRESOLVED #{i}: {info}", flush=True)
    print(f"survivors analyzed: {len(recs)}")
    for key, cnt in stats.most_common(15):
        print(f"  {cnt:6d}  {key}")
    print(f"FEASIBLE: {len(feas)}")
    return feas

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "survivors.jsonl")
