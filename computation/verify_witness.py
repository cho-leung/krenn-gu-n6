"""
Exact verification of a (6,3) witness: coloring + x-vector.

1. Exact check of all 729 IVC sums from the x-vector
   (w(sigma) = 1 for the three monochrome colorings, 0 otherwise).
2. Exact construction of complex weights w_e = prod_M x_M^{a_eM}
   (a = row of the Q-pseudoinverse of the PM-edge incidence matrix),
   and exact check prod_{e in M} w_e == x_M for every PM.
3. Human-readable graph description.

All arithmetic exact (rationals / sympy algebraic numbers).
"""
import sys, json
import sympy as sp
from k6_basics import V, EDGES, PMS, PM_EDGES, EIDX
from search_core import OPTS, ABSENT, MONO_CODE

def verify(coloring, xvec, verbose=True):
    S = [M for M in PM_EDGES if all(coloring[e] is not ABSENT for e in M)]
    idx = {tuple(M): j for j, M in enumerate(S)}
    xmap = {tuple(M): xvec[j] for j, M in enumerate(S)}

    # ---- 1. all 729 IVC sums ----
    sums = {}
    for code in range(3**6):
        sigma = tuple((code // 3**v) % 3 for v in range(6))
        sums[sigma] = sp.Integer(0)
    for M in S:
        c = tuple(coloring[e][0] if e[0] < e[1] else coloring[e][1] for e in M)
        ivc = [None]*6
        for (u, v) in M:
            a, b = coloring[(u, v)]
            ivc[u] = a; ivc[v] = b
        sums[tuple(ivc)] += xmap[tuple(M)]
    ok = True
    for sigma, val in sums.items():
        target = sp.Integer(1) if sigma in [(0,)*6, (1,)*6, (2,)*6] else sp.Integer(0)
        if sp.simplify(val - target) != 0:
            ok = False
            if verbose:
                print(f"  FAIL sigma={sigma} sum={val} expected {target}")
    if verbose:
        print(f"[1] IVC sums over {len(S)} PMs: {'ALL OK' if ok else 'FAILED'}")
    if not ok:
        return False

    # ---- 2. exact weights ----
    present = [e for e in EDGES if coloring[e] is not ABSENT]
    U = sp.Matrix([[1 if e in M else 0 for e in present] for M in S])
    Up = U.pinv()  # Q-pseudoinverse; rows indexed by present edges
    wmap = {}
    for ei, e in enumerate(present):
        a_row = Up.row(ei)   # exponents a_eM
        w = sp.Integer(1)
        for j, M in enumerate(S):
            aM = sp.simplify(a_row[j])
            if aM != 0:
                w *= xvec[j] ** aM
        wmap[e] = sp.simplify(w)
    ok2 = True
    for M in S:
        prod = sp.Integer(1)
        for e in M:
            prod *= wmap[e]
        diff = sp.simplify(prod - xmap[tuple(M)])
        if diff != 0:
            ok2 = False
            if verbose:
                print(f"  FAIL PM {M}: prod(w)={sp.simplify(prod)} vs x={xmap[tuple(M)]}")
    if verbose:
        print(f"[2] weight reconstruction (exact algebraic): {'ALL OK' if ok2 else 'FAILED'}")
    if verbose:
        print("[3] graph description:")
        for e in present:
            print(f"    edge {e}: color {coloring[e]}, weight = {wmap[e]}")
    return ok and ok2

def load_witness_json(path):
    with open(path) as f:
        rec = json.load(f)
    coloring = {}
    for key, val in rec["coloring"].items():
        e = (int(key[0]), int(key[1]))
        coloring[e] = ABSENT if val is None else tuple(val)
    xvec = [sp.sympify(s) for s in rec["witness"]]
    return coloring, xvec

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: verify_witness.py witness.json")
        sys.exit(1)
    coloring, xvec = load_witness_json(sys.argv[1])
    verify(coloring, xvec)
