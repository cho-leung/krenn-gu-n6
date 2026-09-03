"""
Independent cross-checks for the D=4 / D=5 enumerations (2026-09-03).

1. Raw-count cross-check: for D=4, the raw quadruple count is
   sum over the (audited) 5,610 triples T of (2^{c(T)} - 1), where
   c(T) = number of PMs edge-disjoint from the union of T's classes.
   For D=5: quintuples = ordered 1-factorizations = 6 * 5! = 720 (math).
2. Orbit-completeness: canonicalize every raw class and verify its key
   is among the stored reps' keys.
3. Filter cross-check: replay every batch row of every rep with an
   independent naive tuple filter; survivors must match (expect 0).
4. z3: for every rep, encode (b)+(c) in z3 and expect UNSAT.
"""
import pickle, sys, time
import numpy as np
import sympy as sp
from collections import Counter
sys.path.insert(0, "/Users/junhaoliang/Projects/Krenn-Gu/computation")
from k6_basics import EDGES, PM_EDGES, EIDX
from compute_d45 import _struct_ok, canonicalize, enumerate_classes

def check(D):
    print(f"=== D={D} ===")
    with open(f"d{D}_raw.pkl", "rb") as f:
        raw = pickle.load(f)
    with open(f"d{D}_reps.pkl", "rb") as f:
        reps = pickle.load(f)

    # --- 1. raw count ---
    if D == 4:
        # independent raw-triple enumeration (NOT the 24-rep cache)
        mask = [0] * 15
        for m, M in enumerate(PM_EDGES):
            for e in M:
                mask[m] |= 1 << EIDX[e]
        raw_triples = []
        for S0 in range(1, 1 << 15):
            E0 = 0
            for a in range(15):
                if S0 >> a & 1:
                    E0 |= mask[a]
            comp1 = [a for a in range(15) if not (mask[a] & E0)]
            for s1 in range(1, 1 << len(comp1)):
                P1 = [comp1[j] for j in range(len(comp1)) if s1 >> j & 1]
                E1 = 0
                for a in P1:
                    E1 |= mask[a]
                comp2 = [a for j, a in enumerate(comp1) if not (mask[a] & E1)]
                for s2 in range(1, 1 << len(comp2)):
                    P2 = [comp2[j] for j in range(len(comp2)) if s2 >> j & 1]
                    raw_triples.append((tuple(a for a in range(15) if S0 >> a & 1),
                                        tuple(P1), tuple(P2)))
        assert len(raw_triples) == 5610, f"raw triple count {len(raw_triples)} != 5610"
        cnt = 0
        for P0, P1, P2 in raw_triples:
            u = 0
            for P in (P0, P1, P2):
                for m in P:
                    u |= mask[m]
            c = sum(1 for a in range(15) if not (mask[a] & u))
            cnt += (1 << c) - 1
        print(f"  raw count (independent formula): {cnt} vs stored {len(raw)}")
        assert cnt == len(raw), "D=4 raw count mismatch!"
    elif D == 5:
        print(f"  raw count (math): 720 vs stored {len(raw)}")
        assert len(raw) == 720

    # --- 2. orbit completeness ---
    gmaxs = max(len(P) for t in raw for P in t)
    _, keys = canonicalize(raw, D, maxs=gmaxs)
    rep_keys = set()
    for r in reps:
        # canonicalize the single rep with the SAME padding width
        _, rk = canonicalize([r], D, maxs=gmaxs)
        rep_keys |= rk
    missing = keys - rep_keys
    print(f"  orbit completeness: raw keys={len(keys)} rep keys={len(rep_keys)} missing={len(missing)}")
    assert not missing, f"missing orbits: {list(missing)[:2]}"
    assert len(reps) == len(rep_keys), "reps not pairwise inequivalent!"

    # --- 3. filter cross-check on all batch rows ---
    nopt = D * D + 1
    MONO = [(i,) * 6 for i in range(D)]
    def naive_ok(row, pm_class):
        codes = []
        for M in PM_EDGES:
            ivc = [None] * 6
            dead = False
            for (u, v) in M:
                o = int(row[EIDX[(u, v)]])
                if o == nopt - 1:
                    dead = True; break
                a, b = o // D, o % D
                ivc[u] = a; ivc[v] = b
            codes.append(None if dead else tuple(ivc))
        for m in range(15):
            c = codes[m]
            if c is None:
                continue
            for i in range(D):
                if pm_class[m] != i and c == MONO[i]:
                    return False
        cnt = Counter(c for c in codes if c is not None and c not in MONO)
        return all(v >= 2 for v in cnt.values())

    total_rows = 0
    surv_naive = 0
    for classes in reps:
        forced = set()
        for i, P in enumerate(classes):
            for m in P:
                for e in PM_EDGES[m]:
                    forced.add((e, i))
        forced_edges = {e for (e, _) in forced}
        free = [EIDX[e] for e in EDGES if e not in forced_edges]
        F = len(free)
        total_rows += nopt ** F
        pm_class = np.full(15, -1, dtype=np.int64)
        for i, P in enumerate(classes):
            for m in P:
                pm_class[m] = i
        for start in range(0, nopt ** F, 500000):
            rows = np.arange(start, min(start + 500000, nopt ** F), dtype=np.int64)
            assign = np.zeros((len(rows), 15), dtype=np.int64)
            for j, ei in enumerate(free):
                assign[:, ei] = (rows // (nopt ** j)) % nopt
            for (e, i) in forced:
                assign[:, EIDX[e]] = i * D + i
            for r in range(len(rows)):
                row = assign[r]
                if naive_ok(row, pm_class):
                    surv_naive += 1
                    print("  NAIVE SURVIVOR:", classes, row.tolist())
                if _struct_ok(row, pm_class, D, nopt, MONO) != naive_ok(row, pm_class):
                    print("  FILTER DISAGREEMENT:", classes, row.tolist())
                    sys.exit(1)
    print(f"  filter cross-check: {total_rows} rows replayed, naive survivors={surv_naive}")
    assert surv_naive == 0

    # --- 4. z3 per rep ---
    from z3 import Int, Or, And, Not, Solver, sat, unsat
    z3res = []
    for classes in reps:
        forced = {}
        for i, P in enumerate(classes):
            for m in P:
                for e in PM_EDGES[m]:
                    forced[e] = i
        free = [e for e in EDGES if e not in forced]
        s = Solver()
        s.set("timeout", 120000)
        a, b, ab = {}, {}, {}
        for e in free:
            a[e] = Int(f"a{e[0]}{e[1]}")
            b[e] = Int(f"b{e[0]}{e[1]}")
            ab[e] = Int(f"ab{e[0]}{e[1]}")
            s.add(a[e] >= 0, a[e] <= D - 1, b[e] >= 0, b[e] <= D - 1, ab[e] >= 0, ab[e] <= 1)
        def pm_codes(m):
            deads = []
            cols = []
            for (u, v) in PM_EDGES[m]:
                if (u, v) in forced:
                    cols.append((forced[(u, v)], forced[(u, v)]))
                else:
                    deads.append(ab[(u, v)] == 1)
                    cu = Int(f"c{m}_{u}"); cv = Int(f"c{m}_{v}")
                    s.add(cu == a[(u, v)], cv == b[(u, v)])
                    cols.append((cu, cv))
            dead = Or(*deads) if deads else False
            return dead, cols
        pm_class = np.full(15, -1, dtype=np.int64)
        for i, P in enumerate(classes):
            for m in P:
                pm_class[m] = i
        all_codes = []
        for m in range(15):
            dead, cols = pm_codes(m)
            all_codes.append((m, dead, cols))
        def mono_of(m, i):
            dead, cols = all_codes[m]
            return Or(dead, And(*[And(cu == i, cv == i) for (cu, cv) in cols]))
        # (b) no-new-mono
        for m in range(15):
            if pm_class[m] != -1:
                continue
            for i in range(D):
                s.add(Not(And(Not(all_codes[m][1]), And(*[And(cu == i, cv == i) for (cu, cv) in all_codes[m][2]]))))
        # (c) L3: each realized non-mono IVC has a partner
        for m in range(15):
            partners = []
            for m2 in range(15):
                if m2 == m:
                    continue
                eq = True
                for v in range(6):
                    # vertex colors: find the edge of m / m2 covering v
                    cm = Int(f"v{m}_{v}"); cm2 = Int(f"v{m2}_{v}")
                    for (u, w) in PM_EDGES[m]:
                        if u == v: s.add(cm == all_codes[m][2][PM_EDGES[m].index((u, w))][0])
                        if w == v: s.add(cm == all_codes[m][2][PM_EDGES[m].index((u, w))][1])
                    for (u, w) in PM_EDGES[m2]:
                        if u == v: s.add(cm2 == all_codes[m2][2][PM_EDGES[m2].index((u, w))][0])
                        if w == v: s.add(cm2 == all_codes[m2][2][PM_EDGES[m2].index((u, w))][1])
                    eq = And(eq, cm == cm2)
                partners.append(And(Not(all_codes[m2][1]), eq))
            s.add(Or(all_codes[m][1], Or(*partners)))
        res = s.check()
        z3res.append(str(res))
        print(f"  z3 rep {len(z3res)}: {res}")
        assert res == unsat, f"z3 not UNSAT for rep {len(z3res)}!"
    print(f"=== D={D} ALL CHECKS PASS: raw count, orbits, filter, z3 ===\n")

if __name__ == "__main__":
    for D in (4, 5):
        check(D)
    print("D45 CROSS-CHECK COMPLETE")
