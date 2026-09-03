"""
Krenn-Gu (6,3) pipeline -- basic objects on K_6.

Perfect matchings of K_6 (15), edges (15), the PM-edge incidence matrix U,
and the liftability relations (kernel of U^T) that constrain which vectors
x_M = prod_{e in M} w_e are realizable by complex weights.

All claims recorded in the Research OS; see research_os/.
"""
from itertools import combinations
import numpy as np
import sympy as sp

V = list(range(6))
EDGES = sorted(combinations(V, 2))          # 15 edges (u,v) with u<v
EIDX = {e: i for i, e in enumerate(EDGES)}

def pms_of(vertices):
    """All perfect matchings of the complete graph on `vertices` (as frozensets of edges)."""
    out = []
    def rec(rem, cur):
        if not rem:
            out.append(frozenset(cur)); return
        v0 = rem[0]
        for v1 in rem[1:]:
            rec([x for x in rem if x != v0 and x != v1], cur + [(v0, v1)])
    rec(list(vertices), [])
    return out

PMS = pms_of(V)                             # 15 perfect matchings
PM_EDGES = [sorted(M) for M in PMS]         # each PM as sorted edge list

def incidence_matrix(pm_subset=None, edge_subset=None):
    """U[M,e] = 1 if edge e in PM M. Returns sympy Matrix over QQ."""
    pms = pm_subset if pm_subset is not None else PMS
    es  = edge_subset if edge_subset is not None else EDGES
    rows = []
    for M in pms:
        rows.append([1 if e in M else 0 for e in es])
    return sp.Matrix(rows)

def lift_relations(pm_subset, edge_subset):
    """
    Integer-rational basis of ker U^T: vectors c with sum_M c_M * [e in M] = 0.
    Each c encodes the monomial relation  prod_M x_M^{c_M} = 1  that any
    realizable x = (prod_{e in M} w_e) must satisfy.
    """
    U = incidence_matrix(pm_subset, edge_subset)
    return U.T.nullspace()  # sympy vectors over QQ

def ivc_of_pm(pm, coloring):
    """IVC tuple of a perfect matching given edge->(a,b) color pairs.
    coloring: dict edge -> (a,b) (a at lower-indexed endpoint, b at higher)."""
    c = [None]*6
    for (u, v) in pm:
        a, b = coloring[(u, v)]
        c[u] = a; c[v] = b
    return tuple(c)

if __name__ == "__main__":
    print("edges:", len(EDGES), "perfect matchings:", len(PMS))
    U = incidence_matrix()
    print("U shape:", U.shape)
    print("rank(U) over QQ:", U.rank())
    print("det(U) over ZZ:", int(sp.Matrix(U).det()) if U.is_square else "n/a")
    print("rank over ZZ mod 2 (GF(2)):",
          sp.Matrix([[int(x) % 2 for x in row] for row in U.tolist()]).rank())
    rels = lift_relations(PMS, EDGES)
    print("ker(U^T) dim over QQ:", len(rels))
    for r in rels:
        # scale to integers
        den = sp.lcm([sp.fraction(v)[1] for v in r])
        ivec = [int(sp.simplify(v*den)) for v in r]
        g = sp.gcd(ivec)
        ivec = [v//g for v in ivec]
        print("  relation:", ivec)
        print("    -> prod x_M^{c_M} = 1 with c:", ivec)
