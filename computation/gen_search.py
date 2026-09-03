"""
General (6,3) simple-case search over ALL monochrome-class configurations.

For every unordered triple (P0,P1,P2) of pairwise edge-disjoint nonempty PM
subsets of PM(K_6) (up to S_6 symmetry), decide whether SOME assignment of
the remaining edges (9 color-pair options + absent) satisfies:
  (a) no new monochrome PM outside the triple,
  (b) L3: every realized non-mono IVC has >= 2 PMs.
UNSAT at this stage => the configuration class is eliminated (all-nonzero
weights force (b)).  SAT => model -> exact decide() pipeline.
"""
import sys, time, itertools, collections, json
import numpy as np
import sympy as sp
from z3 import Int, Or, And, Not, Solver, sat, unsat
from k6_basics import EDGES, PMS, PM_EDGES, EIDX
from search_core import decide, OPTS, ABSENT, MONO_CODE
from run_search import ivc_codes_batch, l3_and_g_filter

# PM edge masks (15-bit) for conflict checks
EDGE_BIT = {e: 1 << i for i, e in enumerate(EDGES)}
pm_mask = []
for M in PM_EDGES:
    m = 0
    for e in M:
        m |= EDGE_BIT[e]
    pm_mask.append(m)

def enumerate_triples(max_reps=None, cache="triples_cache.pkl"):
    """All class assignments (0,1,2,X) of the 15 PMs with pairwise edge-disjoint
    nonempty classes; canonicalized under S_6. Returns list of (P0,P1,P2).

    Direct construction: enumerate nonempty P0, then nonempty P1 over PMs
    edge-disjoint from P0, then nonempty P2 over PMs edge-disjoint from both.
    (Avoids the 4^15 tree whose leaves are ~99.9% invalid.)"""
    import os, pickle
    if os.path.exists(cache):
        with open(cache, "rb") as f:
            reps = pickle.load(f)
        print(f"loaded {len(reps)} canonical orbit reps from cache", flush=True)
        return reps
    n = len(PMS)
    valid = []
    pm_edge_mask = pm_mask
    pm_touch = [0] * n          # bitmask of PMs sharing an edge with PM m
    for a in range(n):
        t = 0
        for b in range(n):
            if b != a and pm_edge_mask[a] & pm_edge_mask[b]:
                t |= 1 << b
        pm_touch[a] = t

    # subsets with nonempty class 0: iterate as bitmasks
    for S0 in range(1, 1 << n):
        E0 = 0
        for a in range(n):
            if S0 >> a & 1:
                E0 |= pm_edge_mask[a]
        P0 = tuple(a for a in range(n) if S0 >> a & 1)
        # PMs compatible with class 1 (edge-disjoint from class 0)
        compat1 = [a for a in range(n) if not (pm_edge_mask[a] & E0)]
        # iterate nonempty subsets of compat1 as submasks
        c1 = len(compat1)
        for s1 in range(1, 1 << c1):
            E1 = 0
            for j, a in enumerate(compat1):
                if s1 >> j & 1:
                    E1 |= pm_edge_mask[a]
            P1 = tuple(compat1[j] for j in range(c1) if s1 >> j & 1)
            compat2 = [a for j, a in enumerate(compat1) if not (pm_edge_mask[a] & E1)]
            c2 = len(compat2)
            for s2 in range(1, 1 << c2):
                P2 = tuple(compat2[j] for j in range(c2) if s2 >> j & 1)
                valid.append((P0, P1, P2))
    print(f"raw valid triples: {len(valid)}", flush=True)

    # canonicalize under S_6 (vectorized over perms and triples)
    perms = list(itertools.permutations(range(6)))
    edge_inv = {e: i for i, e in enumerate(EDGES)}
    pm_set_to_idx = {tuple(EIDX[e] for e in M): m for m, M in enumerate(PM_EDGES)}
    pm_relabel = np.zeros((len(perms), n), dtype=np.int64)
    for pi_idx, pi in enumerate(perms):
        for m in range(n):
            rel = [edge_inv[tuple(sorted((pi[u], pi[v])))] for (u, v) in PM_EDGES[m]]
            pm_relabel[pi_idx, m] = pm_set_to_idx[tuple(sorted(rel))]

    # pack triples into arrays (pad classes to max size)
    maxs = max(len(p) for P in valid for p in P)
    T = -np.ones((len(valid), 3, maxs), dtype=np.int64)
    for t, P in enumerate(valid):
        for i, Pi in enumerate(P):
            T[t, i, :len(Pi)] = sorted(Pi)

    seen = set()
    reps = []
    CH = 400
    for start in range(0, len(valid), CH):
        Tc = T[start:start + CH]                 # (CH, 3, maxs), padding -1
        rel = np.empty((len(perms), Tc.shape[0], 3, maxs), dtype=np.int64)
        for i in range(3):
            cls = Tc[:, i, :]                    # (CH, maxs)
            mask = cls >= 0
            idx = np.where(mask, cls, 0)
            rel[:, :, i, :] = np.where(mask[None, :, :], pm_relabel[:, idx], -1)
        rel = np.sort(rel, axis=-1)              # -1 padding sorts to front
        keys = rel.reshape(len(perms), Tc.shape[0], -1)
        for j in range(Tc.shape[0]):
            # lexicographically smallest row over the 720 perm keys
            order = np.lexsort(keys[:, j, :].T[::-1])
            bkey = tuple(keys[order[0], j, :].tolist())
            if bkey not in seen:
                seen.add(bkey)
                reps.append(valid[start + j])
        if start % (CH * 50) == 0:
            print(f"canonicalized {start}/{len(valid)} reps={len(reps)}", flush=True)
    print(f"canonical orbit reps: {len(reps)}", flush=True)
    import pickle
    with open(cache, "wb") as f:
        pickle.dump(reps, f)
    return reps

def z3_l3_feasible(P0, P1, P2):
    """Is there a free-edge assignment with no-new-mono and L3?"""
    forced_color = {}
    for i, P in enumerate([P0, P1, P2]):
        for m in P:
            for e in PM_EDGES[m]:
                forced_color[e] = (i, i)
    free = [e for e in EDGES if e not in forced_color]
    free_idx = [EIDX[e] for e in free]

    s = Solver()
    s.set("timeout", 120000)
    a = {}; b = {}; ab = {}
    for e in free:
        a[e] = Int(f"a{e[0]}{e[1]}")
        b[e] = Int(f"b{e[0]}{e[1]}")
        ab[e] = Int(f"ab{e[0]}{e[1]}")
        s.add(a[e] >= 0, a[e] <= 2, b[e] >= 0, b[e] <= 2, ab[e] >= 0, ab[e] <= 1)

    def pm_code(m):
        dead_terms = []
        code_terms = []
        for (u, v) in PM_EDGES[m]:
            if (u, v) in forced_color:
                c1, c2 = forced_color[(u, v)]
                code_terms.append(c1 * 3**u + c2 * 3**v)
            else:
                dead_terms.append(ab[(u, v)] == 1)
                code_terms.append(Int(f"c_{m}_{u}{v}"))
                s.add(Int(f"c_{m}_{u}{v}") == (a[(u, v)] * 3**u + b[(u, v)] * 3**v))
        dead = Or(*dead_terms) if dead_terms else False
        return dead, sum(code_terms)

    classes = [set(P0), set(P1), set(P2)]
    mixed = [m for m in range(len(PMS)) if all(m not in P for P in classes)]
    dead_m, code_m = {}, {}
    for m in mixed:
        dead_m[m], code_m[m] = pm_code(m)

    # (a) no new mono PM
    for m in mixed:
        s.add(Or(dead_m[m], And(*[code_m[m] != mc for mc in MONO_CODE])))
    # (b) L3: every realized non-mono IVC has a partner PM
    for m in mixed:
        partners = [And(Not(dead_m[m2]), code_m[m2] == code_m[m]) for m2 in mixed if m2 != m]
        s.add(Or(dead_m[m], Or(*partners)))

    res = s.check()
    if res == sat:
        model = s.model()
        coloring = {}
        for e in EDGES:
            if e in forced_color:
                coloring[e] = forced_color[e]
            else:
                if model[ab[e]].as_long() == 1:
                    coloring[e] = ABSENT
                else:
                    coloring[e] = (model[a[e]].as_long(), model[b[e]].as_long())
        return "SAT", coloring
    if res == unsat:
        return "UNSAT", None
    return "UNKNOWN", None

def batch_survivors(P0, P1, P2, chunk=200000):
    """Complete batch enumeration over free-edge assignments for one triple.
    Yields (coloring, codes) for assignments passing no-new-mono + L3."""
    forced = set()
    for i, P in enumerate([P0, P1, P2]):
        for m in P:
            for e in PM_EDGES[m]:
                forced.add(e)
    free = [ei for ei, e in enumerate(EDGES) if e not in forced]
    F = len(free)
    nopt = 10
    total = nopt ** F
    pm_class = np.full(len(PMS), -1, dtype=np.int64)
    for i, P in enumerate([P0, P1, P2]):
        for m in P:
            pm_class[m] = i
    for start in range(0, total, chunk):
        rows = np.arange(start, min(start + chunk, total), dtype=np.int64)
        assign = np.zeros((len(rows), 15), dtype=np.int64)
        for j, ei in enumerate(free):
            assign[:, ei] = (rows // (nopt ** j)) % nopt
        for i, P in enumerate([P0, P1, P2]):
            for m in P:
                for e in PM_EDGES[m]:
                    assign[:, EDGES.index(e)] = 4 * i
        codes = ivc_codes_batch(assign)
        ok = l3_and_g_filter(codes, pm_class)
        idx = np.where(ok)[0]
        for j in idx:
            coloring = {}
            for ei, e in enumerate(EDGES):
                if ei in free:
                    o = int(assign[j, ei])
                    coloring[e] = OPTS[o] if o != 9 else ABSENT
            # forced edges: fill from classes
            for i, P in enumerate([P0, P1, P2]):
                for m in P:
                    for e in PM_EDGES[m]:
                        coloring[e] = (i, i)
            yield coloring, codes[j]

def run_all(chunk=200000):
    t0 = time.time()
    reps = enumerate_triples()
    stats = collections.Counter()
    out_f = open("survivors.jsonl", "w")
    n_surv = 0
    n_feas = 0
    for idx, (P0, P1, P2) in enumerate(reps):
        for coloring, _codes in batch_survivors(P0, P1, P2, chunk=chunk):
            n_surv += 1
            rec = {"P": [P0, P1, P2],
                   "coloring": {f"{e[0]}{e[1]}": (None if v is ABSENT else list(v))
                                for e, v in coloring.items()}}
            out_f.write(json.dumps(rec) + "\n")
            verdict, info = decide(coloring)
            stats[verdict] += 1
            if verdict == "FEASIBLE":
                n_feas += 1
                print("*** WITNESS ***", flush=True)
                print("P:", [P0, P1, P2], flush=True)
                print("coloring:", coloring, flush=True)
                print("witness x:", info.get("witness"), flush=True)
            elif verdict == "UNRESOLVED":
                print("UNRESOLVED:", info, flush=True)
        if idx % 20 == 0:
            print(f"rep {idx}/{len(reps)} surv={n_surv} feas={n_feas} {dict(stats)} t={time.time()-t0:.0f}s", flush=True)
    out_f.close()
    print(f"done: reps={len(reps)} survivors={n_surv} feasible={n_feas} {dict(stats)} t={time.time()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    run_all()
