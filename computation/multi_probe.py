"""
Bounded multigraph probe: (1,1,1) mono classes (M0,M1,M2 as in rep 0),
and up to K distinct-pair slots on each free vertex pair.  Question:
can parallel edges satisfy L3 + no-new-mono where the simple case cannot?
"""
from z3 import Int, Or, And, Not, Solver, sat, unsat
from k6_basics import EDGES, PMS, PM_EDGES, EIDX
from search_core import MONO_CODE

def probe(K, timeout_ms=300000, extra_on_forced=False):
    forced = {}
    for M, col in [(PM_EDGES[0], 0), (PM_EDGES[4], 1), (PM_EDGES[8], 2)]:
        for e in M:
            forced[e] = (col, col)
    free = [e for e in EDGES if e not in forced]

    s = Solver()
    s.set("timeout", timeout_ms)
    # slots: for each free vertex pair, K slots, each with pair (a,b) in 0..2 or absent
    A = {}; B = {}; AB = {}
    for e in free:
        for k in range(K):
            A[e, k] = Int(f"a{e}{k}")
            B[e, k] = Int(f"b{e}{k}")
            AB[e, k] = Int(f"ab{e}{k}")
            s.add(A[e, k] >= 0, A[e, k] <= 2, B[e, k] >= 0, B[e, k] <= 2,
                  AB[e, k] >= 0, AB[e, k] <= 1)
        # Lemma P1: same-pair parallel edges merge; forbid duplicates among slots
        for k1 in range(K):
            for k2 in range(k1 + 1, K):
                s.add(Or(AB[e, k1] == 1, AB[e, k2] == 1,
                         A[e, k1] != A[e, k2], B[e, k1] != B[e, k2]))

    # mono PMs must survive: their edges are forced-present single slots
    # PM slots: for each of the 15 PM shapes, choose a slot index per vertex pair
    slot_vars = {}
    code_vars = {}
    dead_vars = {}
    for mi, M in enumerate(PM_EDGES):
        perms = []
        for (u, v) in M:
            if (u, v) in forced:
                perms.append([None])   # single forced slot
            else:
                perms.append(list(range(K)))
        import itertools
        for combo in itertools.product(*perms):
            key = (mi, combo)
            sv = Int(f"s{mi}{combo}")
            slot_vars[key] = sv
            s.add(sv >= 0, sv <= 1)   # 1 = this PM slot is "chosen"?? no: slot presence is derived
    # Simpler model: a PM slot exists iff all its vertex-pair slots are present.
    # Encode per PM-shape slot: presence = AND of slot presences; code = sum of contributions.
    pm_slots = []
    for mi, M in enumerate(PM_EDGES):
        perms = []
        for (u, v) in M:
            if (u, v) in forced:
                perms.append([None])
            else:
                perms.append(list(range(K)))
        import itertools
        for combo in itertools.product(*perms):
            pres = []
            code_terms = []
            ok = True
            for (u, v), kk in zip(M, combo):
                if kk is None:
                    c1, c2 = forced[(u, v)]
                    code_terms.append(c1 * 3**u + c2 * 3**v)
                else:
                    pres.append(AB[(u, v), kk] == 0)
                    code_terms.append(A[(u, v), kk] * 3**u + B[(u, v), kk] * 3**v)
            pm_slots.append((mi, And(*pres), sum(code_terms)))

    # mono classes: PM shapes m0=0, m1=4, m2=8 present with mono codes (forced edges)
    # no-new-mono + L3 over all OTHER pm slots (mixed)
    mixed = [t for t in pm_slots if t[0] not in (0, 4, 8)]
    # new mono PM: a mixed PM slot present whose code is mono
    for mi, pres, code in mixed:
        s.add(Or(Not(pres), And(*[code != mc for mc in MONO_CODE])))
    # L3: every present mixed PM slot has a DIFFERENT present mixed PM slot with same code
    for i, (mi1, pres1, code1) in enumerate(mixed):
        partners = [And(pres2, code2 == code1) for j, (mi2, pres2, code2) in enumerate(mixed) if j != i]
        s.add(Or(Not(pres1), Or(*partners)))

    res = s.check()
    if res == sat:
        model = s.model()
        out = []
        for e in free:
            slots = []
            for k in range(K):
                if model[AB[e, k]].as_long() == 0:
                    slots.append((model[A[e, k]].as_long(), model[B[e, k]].as_long()))
            out.append((e, slots))
        return "SAT", out
    if res == unsat:
        return "UNSAT", None
    return "UNKNOWN", None

if __name__ == "__main__":
    import sys
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    print("K =", K, flush=True)
    import time
    t0 = time.time()
    v, model = probe(K)
    print("result:", v, f"{time.time()-t0:.0f}s", flush=True)
    if model:
        print(model, flush=True)
