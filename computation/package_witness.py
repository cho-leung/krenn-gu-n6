"""
Package a (6,3) witness into a self-contained JSON + verification.
Usage: package_witness.py <witness.json>
Input JSON: {"coloring": {edge: [a,b] or null}, "witness": [x_M strings]}
Output: counterexample/witness_verified.json with exact checks.
"""
import json, sys
import sympy as sp
from k6_basics import V, EDGES, PMS, PM_EDGES
from search_core import OPTS, ABSENT, MONO_CODE
from verify_witness import verify

def main(path):
    with open(path) as f:
        rec = json.load(f)
    coloring = {}
    for key, val in rec["coloring"].items():
        e = (int(key[0]), int(key[1]))
        coloring[e] = ABSENT if val is None else tuple(val)
    xvec = [sp.sympify(s) for s in rec["witness"]]
    ok = verify(coloring, xvec, verbose=True)
    out = {
        "n_vertices": 6,
        "colors": 3,
        "edges": {f"{e[0]}{e[1]}": {"color": list(coloring[e]) if coloring[e] is not ABSENT else None}
                  for e in EDGES},
        "x_witness": [str(v) for v in xvec],
        "exact_ivc_sums_verified": bool(ok),
        "note": "w(sigma)=1 for sigma in {000,111,222} and 0 otherwise, exact arithmetic; "
                "see computation/verify_witness.py",
    }
    outpath = "../counterexample/witness_verified.json"
    with open(outpath, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {outpath}")
    return ok

if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1]) else 1)
