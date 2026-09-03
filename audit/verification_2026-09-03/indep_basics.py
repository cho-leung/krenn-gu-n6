"""
INDEPENDENT verification of K_6 basics for the (6,3) audit (2026-09-03).

Fresh implementation (no import of computation/*.py):
  - PM enumeration of K_6 (expect 15)
  - PM-edge incidence matrix U, rank over QQ (expect 10)
  - ker U^T (expect dim 5), relations as integer vectors
  - check the 1-factorization-pair span claim
"""
from itertools import combinations
import sympy as sp

V = list(range(6))
EDGES = sorted(combinations(V, 2))

def pms(vertices):
    out = []
    def rec(rem, cur):
        if not rem:
            out.append(frozenset(cur)); return
        v0 = rem[0]
        for v1 in rem[1:]:
            rec([x for x in rem if x != v0 and x != v1], cur + [(v0, v1)])
    rec(list(vertices), [])
    return out

PMS = sorted(pms(V), key=lambda M: sorted(tuple(sorted(e) for e in M)))
PM_LIST = [sorted(M) for M in PMS]
print("n_edges =", len(EDGES), " n_PMs =", len(PMS))
assert len(EDGES) == 15 and len(PMS) == 15

U = sp.Matrix([[1 if e in M else 0 for e in EDGES] for M in PM_LIST])
print("U shape:", U.shape, " rank(U) over QQ =", U.rank())
Uf2 = sp.Matrix([[int(x) % 2 for x in row] for row in U.tolist()])
print("rank(U) over F2 =", Uf2.rank())
ker = U.T.nullspace()
print("dim ker U^T =", len(ker))
for r in ker:
    den = sp.lcm([sp.fraction(v)[1] for v in r])
    ivec = [int(sp.simplify(v * den)) for v in r]
    g = sp.gcd(ivec)
    print("  rel:", [v // g for v in ivec])

# --- 1-factorizations of K_6: 5 pairwise edge-disjoint PMs partitioning E ---
facts = []
used = set()
def find_factorizations(avail, cur):
    # avail: set of PM indices; choose a disjoint cover of all 15 edges
    cover = set()
    for m in cur:
        cover |= set(PM_LIST[m])
    if len(cover) == 15:
        facts.append(tuple(cur)); return
    # smallest uncovered edge must be covered by the next PM
    e0 = next(e for e in EDGES if e not in cover)
    for m in avail:
        if e0 in PM_LIST[m] and not (set(PM_LIST[m]) & cover):
            find_factorizations([a for a in avail if a != m], cur + [m])
find_factorizations(list(range(15)), [])
print("1-factorizations found:", len(facts), " (literature: 6)")
# pair-relations: prod_{M in F} x_M = prod_{M in F'} x_M  =>  c = 1_F - 1_F'
pair_rels = []
for i, F in enumerate(facts):
    for F2 in facts[i+1:]:
        c = [0]*15
        for m in F: c[m] += 1
        for m in F2: c[m] -= 1
        pair_rels.append(c)
# does the pair-relation span equal ker U^T?
M = sp.Matrix(pair_rels)
print("rank of pair-relation span:", M.rank(), " (expect 5 = dim ker U^T)")
assert M.rank() == len(ker) == 5
print("BASICS OK")
