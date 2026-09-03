"""
INDEPENDENT verification of the class enumeration for the (6,3) audit.

Claims under audit (computation/gen_search.py):
  C1: the number of ordered triples (P0,P1,P2) of nonempty, pairwise
      edge-disjoint PM subsets is 5,610.
  C2: the 24 reps in computation/triples_cache.pkl are a complete,
      non-redundant set of S_6 orbit representatives (colors fixed).

Fresh implementation: independent enumeration + independent canonicalization.
"""
import itertools, pickle, sys
sys.path.insert(0, "/Users/junhaoliang/Projects/Krenn-Gu/computation")
from k6_basics import EDGES, PM_EDGES, EIDX   # data only (edge/PM lists); logic below is ours

N = len(PM_EDGES)
mask = [0] * N
for m, M in enumerate(PM_EDGES):
    for e in M:
        mask[m] |= 1 << EIDX[e]

# ---- independent raw enumeration ------------------------------------------
# For each PM class assignment (0,1,2,X) of the 15 PMs with pairwise
# edge-disjoint nonempty classes, count ordered triples.
raw = []
for S0 in range(1, 1 << N):
    E0 = 0
    for a in range(N):
        if S0 >> a & 1:
            E0 |= mask[a]
    comp1 = [a for a in range(N) if not (mask[a] & E0)]
    for s1 in range(1, 1 << len(comp1)):
        P1 = [comp1[j] for j in range(len(comp1)) if s1 >> j & 1]
        E1 = 0
        for a in P1:
            E1 |= mask[a]
        comp2 = [a for j, a in enumerate(comp1) if not (mask[a] & E1)]
        for s2 in range(1, 1 << len(comp2)):
            P2 = [comp2[j] for j in range(len(comp2)) if s2 >> j & 1]
            raw.append((tuple(a for a in range(N) if S0 >> a & 1),
                        tuple(P1), tuple(P2)))
print("raw valid triples:", len(raw))

# ---- independent canonicalization under S_6 (colors fixed) -----------------
edge_inv = {e: i for i, e in enumerate(EDGES)}
pm_lookup = {tuple(EIDX[e] for e in M): m for m, M in enumerate(PM_EDGES)}
def canon(P0, P1, P2):
    best = None
    for pi in itertools.permutations(range(6)):
        def relabel(m):
            rel = [edge_inv[tuple(sorted((pi[u], pi[v])))] for (u, v) in PM_EDGES[m]]
            return pm_lookup[tuple(sorted(rel))]
        key = (tuple(sorted(relabel(m) for m in P0)),
               tuple(sorted(relabel(m) for m in P1)),
               tuple(sorted(relabel(m) for m in P2)))
        if best is None or key < best:
            best = key
    return best

canon_of_raw = set()
for P in raw:
    canon_of_raw.add(canon(*P))
print("distinct canonical forms of all raw triples:", len(canon_of_raw))

# ---- compare with the cached 24 reps ---------------------------------------
with open("/Users/junhaoliang/Projects/Krenn-Gu/computation/triples_cache.pkl", "rb") as f:
    cached = pickle.load(f)
cached_canons = set()
for P0, P1, P2 in cached:
    cached_canons.add(canon(P0, P1, P2))
print("distinct canonical forms of cached reps:", len(cached_canons))

valid = all(len(p) > 0 for P in cached for p in P)
disjoint = True
for P0, P1, P2 in cached:
    E0 = set().union(*[set(PM_EDGES[m]) for m in P0])
    E1 = set().union(*[set(PM_EDGES[m]) for m in P1])
    E2 = set().union(*[set(PM_EDGES[m]) for m in P2])
    if E0 & E1 or E0 & E2 or E1 & E2:
        disjoint = False
print("cached reps all valid & pairwise-disjoint classes:", valid and disjoint)

cover = cached_canons == canon_of_raw
print("cached reps cover ALL orbits exactly:", cover)
if not cover:
    missing = canon_of_raw - cached_canons
    extra = cached_canons - canon_of_raw
    print("missing:", len(missing), "extra:", len(extra))
    if missing:
        print("first missing:", next(iter(missing)))
    sys.exit(1)
print("TRIPLES OK: 5,610 raw == %d; 24 reps complete & non-redundant" % len(raw))
