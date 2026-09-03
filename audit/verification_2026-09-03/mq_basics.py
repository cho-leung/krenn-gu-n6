"""
mq_basics.py -- self-contained basics for the MULTIGRAPH (6,3) decision.
Built for the Q1 attack (parallel_edges_Q1_attack_2026-09-03.md).
Independent re-derivation of K_6 data (no imports from computation/).

A multigraph on vertices 0..5: per vertex pair e={u,v} (u<v) a set of
"slots" (parallel edges); each slot has an ordered color pair (a,b),
a at u and b at v (u<v).  Slots at a pair carry DISTINCT color pairs
(same-pair merge lemma P1).  A PM of the multigraph = (shape, slot choice
per pair in shape); x_M = product of slot weights along M.
"""
from itertools import combinations, product

V = list(range(6))
EDGES = list(combinations(V, 2))          # 15 pairs (u,v), u<v
EIDX = {e: i for i, e in enumerate(EDGES)}

def _pms(verts):
    out = []
    def rec(rem, cur):
        if not rem:
            out.append(frozenset(cur)); return
        v0 = rem[0]
        for v1 in rem[1:]:
            rec([x for x in rem if x != v0 and x != v1], cur + [(v0, v1)])
    rec(list(verts), [])
    return out

PMS = _pms(V)                              # 15 perfect matchings of K_6
PM_EDGES = [sorted(M) for M in PMS]        # shapes as sorted pair lists
SHAPE_PAIRS = [tuple(e for e in M) for M in PM_EDGES]  # canonical edge order

def slot_code_term(e, color):
    """contribution of color `color` at vertex e[0] or e[1] (base-3 digit weight)."""
    u, v = e
    return color * 3**u + color * 3**v

def vertex_of_pair(e, x):
    return e[0] == x, e[1] == x   # (is_lower, is_upper)

def pm_instances(slot_coloring):
    """
    slot_coloring: dict pair -> tuple of ordered color pairs (a,b), a at
    lower-indexed endpoint.  Present slots = those listed (>=1).  Returns
    list of PM instances: dicts with keys
       shape   : shape index in 0..14
       combo   : tuple (pair -> slot index) used
       edges   : tuple of slots used as ((pair, slotidx), ...)
       code    : base-3 code of the IVC (6 base-3 digits)
       digits  : IVC as tuple of 6 colors
    Every PM instance = (shape, choice of one slot per pair of shape),
    for pairs of the shape that have >= 1 present slot.
    """
    inst = []
    for si, shape in enumerate(SHAPE_PAIRS):
        per_pair_opts = []
        for e in shape:
            sl = slot_coloring.get(e, ())
            per_pair_opts.append([(j, sl[j]) for j in range(len(sl))])
        for combo in product(*per_pair_opts):
            digits = [None] * 6
            edges = []
            for e, (j, (a, b)) in zip(shape, combo):
                edges.append((e, j))
                if digits[e[0]] is not None or digits[e[1]] is not None:
                    raise ValueError("shape not a PM?")
                digits[e[0]] = a
                digits[e[1]] = b
            t = tuple(digits)
            code = sum(c * 3**x for x, c in enumerate(t))
            inst.append({"shape": si, "combo": tuple(j for _, j in combo),
                         "edges": tuple(edges), "digits": t, "code": code})
    return inst

def pm_list_from_coloring(coloring):
    """
    coloring: dict pair -> color pair (a,b) or None for absent (simple case).
    Convenience wrapper producing slot_coloring and instances.
    """
    sc = {e: (v,) for e, v in coloring.items() if v is not None}
    return sc, pm_instances(sc)

MONO_DIGITS = [tuple([i] * 6) for i in range(3)]
MONO_CODE = [sum(i * 3**x for x in range(6)) for i in range(3)]
