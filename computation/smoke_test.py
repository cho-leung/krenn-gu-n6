"""Smoke tests for search_core.decide on hand-verified cases."""
from k6_basics import EDGES
from search_core import decide, ABSENT, OPTS

def coloring_from(full):
    """full: list of option indices per edge (9 = absent)."""
    return {e: (OPTS[o] if o != 9 else ABSENT) for e, o in zip(EDGES, full)}

# Test 1: three disjoint monochrome PMs, everything else absent.
# M0={01,23,45}, M1={02,14,35}, M2={03,15,24}
# Hand analysis: mixed PM {01,24,35} realizes a non-mono IVC alone -> INFEASIBLE.
o = lambda pair: OPTS.index(pair)
c1 = [9]*15
for e in [(0,1),(2,3),(4,5)]: c1[EDGES.index(e)] = o((0,0))
for e in [(0,2),(1,4),(3,5)]: c1[EDGES.index(e)] = o((1,1))
for e in [(0,3),(1,5),(2,4)]: c1[EDGES.index(e)] = o((2,2))
v, info = decide(coloring_from(c1))
print("T1 (3 disjoint mono PMs, rest absent):", v, info.get("reason"))
assert v == "INFEASIBLE", "T1 expected INFEASIBLE (singleton mixed IVC)"

# Test 2: all edges color (0,0): missing colors 1,2 -> INFEASIBLE
c2 = [o((0,0))]*15
v, info = decide(coloring_from(c2))
print("T2 (all mono 0):", v, info.get("reason"))
assert v == "INFEASIBLE"

# Test 3: all edges color (0,1): no monochrome PM at all -> INFEASIBLE
c3 = [o((0,1))]*15
v, info = decide(coloring_from(c3))
print("T3 (all bichromatic 0|1):", v, info.get("reason"))
assert v == "INFEASIBLE"

# Test 4: 3 disjoint mono PMs but bichromatic completion chosen so that the
# extra PMs cancel pairwise.  Take M0,M1,M2 as above; remaining 6 free edges
# are 04,05,12,13,25,34 forming PMs {04,13,25} and {05,12,34}.
# Assign them pairs (0,1)/(1,0) so both have the same non-mono IVC.
# {04:(0,1), 13:(1,0), 25:(0,1)} -> IVC: v0:0,v4:1, v1:1,v3:0, v2:0,v5:1 = (0,1,0,0,1,1)
# {05:(0,1), 12:(1,0), 34:(0,1)} -> IVC: v0:0,v5:1, v1:1,v2:0, v3:0,v4:1 = (0,1,0,0,1,1)
# But the other mixed PMs (e.g. {01,24,35}) are singleton groups -> still INFEASIBLE.
c4 = c1[:]
for e,p in [((0,4),(0,1)),((1,3),(1,0)),((2,5),(0,1)),
            ((0,5),(0,1)),((1,2),(1,0)),((3,4),(0,1))]:
    c4[EDGES.index(e)] = o(p)
v, info = decide(coloring_from(c4))
print("T4 (bichromatic completion):", v, info.get("reason"))

print("smoke tests passed")
