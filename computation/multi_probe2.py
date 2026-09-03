"""
Multigraph probe v2: (1,1,1) mono classes, distinct-pair slots allowed on
ALL vertex pairs (forced pairs keep their (i,i) slot plus up to K-1 extra
distinct slots).  L3 + no-new-mono at the merged (distinct-pair) level.
"""
import itertools, time
from z3 import Int, Or, And, Not, Solver, sat, unsat
from k6_basics import EDGES, PMS, PM_EDGES
from search_core import MONO_CODE

def probe(K, timeout_ms=3600000):
    forced = {}
    for M, col in [(PM_EDGES[0], 0), (PM_EDGES[4], 1), (PM_EDGES[8], 2)]:
        for e in M:
            forced[e] = (col, col)

    s = Solver()
    s.set("timeout", timeout_ms)
    A = {}; B = {}; AB = {}
    # slots per vertex pair: forced pairs: slot 0 = forced pair, slots 1..K-1 extra;
    # free pairs: slots 0..K-1 all free
    for e in EDGES:
        k0 = 0 if e in forced else -1   # slot index of the forced pair, or none
        slots = []
        for k in range(K):
            if k == k0:
                slots.append(("forced", forced[e]))
            else:
                a = Int(f"a{e[0]}{e[1]}_{k}")
                b = Int(f"b{e[0]}{e[1]}_{k}")
                ab = Int(f"ab{e[0]}{e[1]}_{k}")
                A[e, k] = a; B[e, k] = b; AB[e, k] = ab
                s.add(a >= 0, a <= 2, b >= 0, b <= 2, ab >= 0, ab <= 1)
                slots.append(("var", k))
        # distinctness among all PRESENT slot pairs (merged level, Lemma P1)
        pairs = []
        if e in forced:
            pairs.append((0, forced[e]))
        for k in range(K):
            if k != k0:
                pairs.append((k, None))
        for i1, (k1, p1) in enumerate(pairs):
            for k2, p2 in pairs[i1 + 1:]:
                if p1 is not None and p2 is not None:
                    continue
                # slot k1 present with pair p1, slot k2 present with pair p2: pairs differ
                def present(k):
                    return True if (k == k0) else (AB[e, k] == 0)
                def pairvars(k, p):
                    if p is not None:
                        return (IntVal if False else p[0], p[1])
                    return (A[e, k], B[e, k])
                s.add(Or(Not(present(k1)), Not(present(k2)),
                         pairvars(k1, p1)[0] != pairvars(k2, p2)[0],
                         pairvars(k1, p1)[1] != pairvars(k2, p2)[1]))

    # PM slots: per shape, choose one slot per vertex pair
    # (forced pairs: forced slot + K-1 extra slots; free pairs: K slots)
    def slot_choices(e):
        if e in forced:
            k0 = 0
            return [(0, forced[e])] + [(k, None) for k in range(1, K)]
        return [(k, None) for k in range(K)]

    pm_slots = []
    for mi, M in enumerate(PM_EDGES):
        for combo in itertools.product(*[slot_choices(e) for e in M]):
            pres = []
            code_terms = []
            pure = True
            for (u, v), (k, p) in zip(M, combo):
                if p is not None:
                    code_terms.append(p[0] * 3**u + p[1] * 3**v)
                else:
                    pure = False
                    pres.append(AB[(u, v), k] == 0)
                    code_terms.append(A[(u, v), k] * 3**u + B[(u, v), k] * 3**v)
            pm_slots.append((mi, pure, And(*pres), sum(code_terms)))

    # mixed slots = all slots except the three pure-forced mono class PMs
    mixed = [t for t in pm_slots if not (t[1] and t[0] in (0, 4, 8))]
    for mi, _pure, pres, code in mixed:
        s.add(Or(Not(pres), And(*[code != mc for mc in MONO_CODE])))
    for i, (_mi1, _p1, pres1, code1) in enumerate(mixed):
        partners = [And(pres2, code2 == code1) for j, (_m2, _p2, pres2, code2) in enumerate(mixed) if j != i]
        s.add(Or(Not(pres1), Or(*partners)))

    t0 = time.time()
    res = s.check()
    print("checked in", int(time.time() - t0), "s", flush=True)
    if res == sat:
        model = s.model()
        out = {}
        for e in EDGES:
            slots = []
            k0 = 0 if e in forced else -1
            if k0 is not None:
                slots.append(forced[e])
            for k in range(K):
                if k != k0 and model[AB[e, k]].as_long() == 0:
                    slots.append((model[A[e, k]].as_long(), model[B[e, k]].as_long()))
            out[e] = slots
        return "SAT", out
    if res == unsat:
        return "UNSAT", None
    return "UNKNOWN", None

if __name__ == "__main__":
    import sys
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    v, model = probe(K)
    print("K =", K, "->", v, flush=True)
    if model:
        for e in EDGES:
            print(e, model[e], flush=True)
