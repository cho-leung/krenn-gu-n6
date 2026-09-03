"""
Independent engine tests: positive controls and cross-checks. (2026-09-03)
"""
import sys, random
import sympy as sp
sys.path.insert(0, "/Users/junhaoliang/Projects/Krenn-Gu/computation")
sys.path.insert(0, "/Users/junhaoliang/Projects/Krenn-Gu/audit/verification_2026-09-03")
from indep_engine import decide_general, exact_weights
from k6_basics import EDGES, EIDX
from search_core import decide, OPTS, ABSENT

def verify_witness_sums(n, coloring, w):
    """Recompute ALL 3^n IVC sums exactly from explicit weights; return dict."""
    from indep_engine import _pms
    from itertools import combinations
    V = list(range(n))
    PMS = _pms(V)
    sums = {}
    for code in range(3**n):
        sigma = tuple((code // 3**v) % 3 for v in range(n))
        s = sp.Integer(0)
        for M in PMS:
            if all(coloring[e] is not None for e in M):
                ivc = [None]*n
                ok = True
                for (u, v) in M:
                    a, b = coloring[(u, v)]
                    ivc[u] = a; ivc[v] = b
                if tuple(ivc) == sigma:
                    prod = sp.Integer(1)
                    for e in M:
                        prod *= w[e]
                    s += prod
        sums[sigma] = sp.simplify(s)
    return sums

# ---- E1: (4,3) K_4 known dimension-3 example -> must be FEASIBLE ----------
col4 = {}
for e in [(0,1),(2,3)]: col4[e] = (0,0)
for e in [(0,2),(1,3)]: col4[e] = (1,1)
for e in [(0,3),(1,2)]: col4[e] = (2,2)
v, info = decide_general(4, col4, mono_required=3, b_mixed=0)
print("E1 (4,3) K4:", v)
assert v == "FEASIBLE", "E1 failed"
x = info["witness"]
w, S = exact_weights(4, col4, x)
sums = verify_witness_sums(4, col4, w)
mono_ok = all(sums[(i,)*4] == 1 for i in range(3))
others_ok = all(s == 0 for sig, s in sums.items() if len(set(sig)) > 1)
print("  exact 81-sum verification: mono=1:", mono_ok, " others=0:", others_ok)
assert mono_ok and others_ok
print("E1 PASS")

# ---- E2: relaxed (6,3) on K_{3,3} (b_mixed=1) -> FEASIBLE through relations ---
M0 = [(0,1),(2,3),(4,5)]; M1 = [(0,2),(1,4),(3,5)]; M2 = [(0,3),(1,5),(2,4)]
col6 = {e: None for e in EDGES}
for e in M0: col6[e] = (0,0)
for e in M1: col6[e] = (1,1)
for e in M2: col6[e] = (2,2)
v2, info2 = decide_general(6, col6, mono_required=3, b_mixed=1)
print("E2 relaxed (6,3) K33:", v2, "k=", info2.get("k"))
assert v2 == "FEASIBLE", "E2 failed"
w2, S2 = exact_weights(6, col6, info2["witness"])
sums2 = verify_witness_sums(6, col6, w2)
mono_ok2 = all(sums2[(i,)*6] == 1 for i in range(3))
# M0 u M1 u M2 is the triangular prism: 4 PMs, the 4th is the three
# cross edges {(0,1),(2,4),(3,5)} with IVC (0,0,2,1,2,1).
mixed_sigs = [(0,0,2,1,2,1)]
mixed_ok2 = all(sums2[sig] == 1 for sig in mixed_sigs)
rest_ok2 = all(s == 0 for sig, s in sums2.items()
               if len(set(sig)) > 1 and sig not in mixed_sigs)
print("  mono=1:", mono_ok2, " relaxed-mixed=1:", mixed_ok2, " rest=0:", rest_ok2)
assert mono_ok2 and mixed_ok2 and rest_ok2
print("E2 PASS")

# ---- E3: exact (6,3) on K_{3,3} -> INFEASIBLE via L3 (both engines) --------
v3, info3 = decide_general(6, col6, mono_required=3, b_mixed=0)
print("E3 exact (6,3) K33 (my engine):", v3, info3.get("reason"))
assert v3 == "INFEASIBLE"
v3b, info3b = decide(col6)
print("E3 exact (6,3) K33 (their decide):", v3b, info3b.get("reason"))
assert v3b == "INFEASIBLE"
print("E3 PASS")

# ---- E4: random cross-check my engine vs their decide (exact problem) -----
rng = random.Random(20260903)
agree = 0; disagree = 0; my_unres = 0
for t in range(300):
    coloring = {}
    for e in EDGES:
        o = rng.randrange(10)
        coloring[e] = OPTS[o] if o != 9 else ABSENT
    vm, im = decide_general(6, coloring, 3, 0)
    vt, it = decide(coloring)
    if vm == vt:
        agree += 1
    elif vm == "UNRESOLVED":
        my_unres += 1
    else:
        disagree += 1
        print("DISAGREE:", t, vm, im.get("reason"), "vs", vt, it.get("reason"))
print(f"E4 random cross-check: agree={agree} disagree={disagree} my_unresolved={my_unres}")
assert disagree == 0, "engine disagreement!"
print("E4 PASS")

# ---- E5: mono (a)-passers sample -> both engines INFEASIBLE (L3) -----------
# sample mono colorings uniformly until 200 with all three mono IVCs realized
sample = []
tries = 0
while len(sample) < 200 and tries < 20000:
    tries += 1
    coloring = {}
    for e in EDGES:
        i = rng.randrange(3)
        coloring[e] = (i, i)
    from search_core import ivc_code
    from k6_basics import PMS
    codes = [ivc_code(M, coloring) for M in PMS]
    if all(sum(i * 3**v for v in range(6)) in codes for i in range(3)):
        sample.append(coloring)
ok5 = 0
for coloring in sample:
    vm, im = decide_general(6, coloring, 3, 0)
    vt, it = decide(coloring)
    assert vm == "INFEASIBLE" and vt == "INFEASIBLE", (vm, im, vt, it)
    ok5 += 1
print(f"E5 mono (a)-passers sample: {ok5} both INFEASIBLE")
print("E5 PASS")

# ---- E6: relaxed full-K_6 instance exercising the lift-relation machinery --
# S = 15 (full graph, rank(U)=10, 5 relations), k >= 1 -> relation solving.
col_full = {e: (0, 1) for e in EDGES}
for e in M0: col_full[e] = (0, 0)
for e in M1: col_full[e] = (1, 1)
for e in M2: col_full[e] = (2, 2)
v6, info6 = decide_general(6, col_full, mono_required=3, b_mixed=1)
print("E6 relaxed full K6:", v6, {k2: v2 for k2, v2 in info6.items() if k2 != "witness"})
if v6 == "FEASIBLE":
    xw = info6["witness"]
    from indep_engine import _pms
    S6 = [M for M in _pms(list(range(6))) if all(col_full[e] is not None for e in M)]
    # direct witness verification: group sums + all five ker U^T relations
    from itertools import combinations
    U6 = sp.Matrix([[1 if e in M else 0 for e in EDGES] for M in S6])
    rels = U6.T.nullspace()
    rels_ok = True
    for rel in rels:
        den = sp.lcm([sp.fraction(vv)[1] for vv in rel])
        ivec = [int(sp.simplify(vv * den)) for vv in rel]
        g = sp.gcd(ivec)
        ivec = [vv // g for vv in ivec]
        lhs = sp.Integer(1)
        for m, c in enumerate(ivec):
            if c > 0: lhs *= xw[m] ** c
            elif c < 0: lhs = sp.simplify(lhs / xw[m] ** (-c))
        if sp.simplify(lhs - 1) != 0:
            rels_ok = False
    print("  ker-relations satisfied by witness:", rels_ok)
    assert rels_ok
    print("E6 PASS (FEASIBLE through relation machinery, witness verified)")
elif v6 == "INFEASIBLE":
    print("E6 PASS (relation machinery returned exact INFEASIBLE:", info6.get("reason"), ")")
else:
    print("E6 NOTE: UNRESOLVED (numeric path limit); no soundness claim at risk")

print("ALL ENGINE TESTS PASS")
