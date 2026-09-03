"""
Batch search over colorings of K_6 for the (6,3) problem.

Modes:
  mono  : validate pipeline against known result -- monochrome edges only,
          expect UNSAT (Cervera-Lierta et al., Quantum 6:836 (2022)).
  t111  : full setting, |P0|=|P1|=|P2|=1 (three single-PM monochrome classes),
          bichromatic edges + absent edges allowed.
"""
import sys, time, itertools, json
import numpy as np
import sympy as sp
from k6_basics import V, EDGES, PMS, PM_EDGES
from search_core import decide, ivc_code, MONO_CODE, ABSENT, OPT_A, OPT_B, OPTS

# ---- vectorized IVC codes -------------------------------------------------
# T[e, o] = contribution of edge e=(u,v) under option o (0..8); o=9 -> ABSENT
T = np.zeros((15, 10), dtype=np.int64)
for ei, (u, v) in enumerate(EDGES):
    for o, (a, b) in enumerate(OPTS):
        T[ei, o] = a * 3**u + b * 3**v
    T[ei, 9] = 0  # absent

PM_EIDX = [[EDGES.index(e) for e in M] for M in PM_EDGES]  # edge indices per PM

def ivc_codes_batch(assign):
    """assign: (N,15) int array of option indices (0..8, 9=absent) -> (N,15) codes,
    with -1 marking dead PMs (those containing an absent edge)."""
    N = assign.shape[0]
    contrib = T[np.arange(15)[None, :], assign]      # (N,15)
    dead = np.zeros((N, 15), dtype=bool)
    codes = np.zeros((N, 15), dtype=np.int64)
    for mi, eidx in enumerate(PM_EIDX):
        e1, e2, e3 = eidx
        codes[:, mi] = contrib[:, e1] + contrib[:, e2] + contrib[:, e3]
        dead[:, mi] = (assign[:, e1] == 9) | (assign[:, e2] == 9) | (assign[:, e3] == 9)
    codes[dead] = -1
    return codes

def l3_group_filter(codes):
    """L3 only: every realized non-mono IVC group has >= 2 PMs (all-nonzero weights)."""
    N = codes.shape[0]
    c = codes.copy()
    c[codes == -1] = 10**9  # dead -> sentinel
    for mc in MONO_CODE:
        c[codes == mc] = 10**9
    s = np.sort(c, axis=1)
    n = s.shape[1]
    # left_ok[j] = s[j] differs from s[j-1] (True at border j=0);
    # right_ok[j] = s[j] differs from s[j+1] (True at border j=n-1).
    # A value is a singleton iff it differs from BOTH neighbors.
    left_ok = np.ones((N, n), dtype=bool)
    right_ok = np.ones((N, n), dtype=bool)
    left_ok[:, 1:] = s[:, 1:] != s[:, :-1]
    right_ok[:, :-1] = s[:, 1:] != s[:, :-1]
    sing = (s != 10**9) & left_ok & right_ok
    return ~sing.any(axis=1)

def l3_and_g_filter(codes, pm_class):
    """
    pm_class: array of PM classes 0,1,2 for mono PMs (fixed per triple), -1 mixed.
    Returns per-row booleans: no new mono PMs among mixed; all non-mono realized
    IVC groups have size >= 2; g = number of distinct realized non-mono codes.
    """
    N = codes.shape[0]
    keep = np.ones(N, dtype=bool)
    # 1) mixed PMs must not be monochrome (would create new mono PMs)
    for i in range(3):
        is_mixed = (pm_class != i)
        bad = is_mixed[None, :] & (codes == MONO_CODE[i])
        keep &= ~bad.any(axis=1)
    # 2) L3 grouping
    keep &= l3_group_filter(codes)
    return keep

def distinct_g(codes):
    """number of distinct non-mono realized IVC codes per row."""
    c = codes.copy()
    for mc in MONO_CODE:
        c[codes == mc] = -1
    s = np.sort(c, axis=1)
    s = np.where(s < 0, 10**9, s)
    g = np.zeros(s.shape[0], dtype=np.int64)
    n = s.shape[1]
    d = s[:, 1:] != s[:, :-1]
    g = 1 + d.sum(axis=1)
    # if no non-mono codes: 0
    empty = (s == 10**9).all(axis=1)
    g[empty] = 0
    return g

# ---- mono validation: enumerate all 3^15 monochrome colorings -------------
def _survivor_to_coloring(assign_row):
    coloring = {}
    for ei, e in enumerate(EDGES):
        o = int(assign_row[ei])
        coloring[e] = OPTS[o] if o != 9 else ABSENT
    return coloring

def _decide_worker(args):
    coloring = _survivor_to_coloring(args)
    try:
        return decide(coloring)
    except Exception as ex:
        return ("ERROR", {"exception": str(ex), "coloring": str(coloring)})

def run_mono(chunk=500000, max_rows=None, nprocs=None):
    import multiprocessing as mp
    if nprocs is None:
        nprocs = min(8, max(1, mp.cpu_count() - 2))
    t0 = time.time()
    n_feasible = 0
    n_surv = 0
    n_rows = 0
    limit = max_rows if max_rows is not None else 3**15
    survivors = []
    for start in range(0, limit, chunk):
        rows = np.arange(start, min(start + chunk, limit), dtype=np.int64)
        assign = np.zeros((len(rows), 15), dtype=np.int64)
        for ei in range(15):
            assign[:, ei] = (rows // (3**ei)) % 3
        # mono options: (0,0)->0, (1,1)->4, (2,2)->8
        assign = assign * 4
        codes = ivc_codes_batch(assign)
        ok = np.ones(len(rows), dtype=bool)
        for i in range(3):
            ok &= (codes == MONO_CODE[i]).any(axis=1)   # each color realized
        ok &= l3_group_filter(codes)
        idx = np.where(ok)[0]
        n_rows += len(rows)
        survivors.extend(assign[j].copy() for j in idx)
        if start % (chunk * 20) == 0:
            print(f"mono scan {n_rows}/{limit} survivors={len(survivors)} t={time.time()-t0:.0f}s", flush=True)
    print(f"mono scan done: rows={n_rows} survivors={len(survivors)} t={time.time()-t0:.0f}s; deciding...", flush=True)
    with mp.Pool(nprocs) as pool:
        for verdict, info in pool.imap_unordered(_decide_worker, survivors, chunksize=64):
            n_surv += 1
            if verdict == "FEASIBLE":
                n_feasible += 1
                print("MONO FEASIBLE?!", info, flush=True)
            elif verdict == "UNRESOLVED":
                print("MONO UNRESOLVED:", info, flush=True)
            if n_surv % 20000 == 0:
                print(f"mono decide {n_surv}/{len(survivors)} feasible={n_feasible} t={time.time()-t0:.0f}s", flush=True)
    print(f"mono done: rows={n_rows} survivors={n_surv} feasible={n_feasible} t={time.time()-t0:.0f}s")

# ---- (1,1,1) search: three single-PM mono classes -------------------------
def canonical_triple(P0, P1, P2):
    """Canonical form under S_6 vertex permutations (colors fixed)."""
    best = None
    for pi in itertools.permutations(range(6)):
        # relabel vertices: edge (u,v) -> sorted((pi[u],pi[v]))
        inv = {e: i for i, e in enumerate(EDGES)}
        def relabel_pm(pidx):
            M = PM_EDGES[pidx]
            rel = [inv[tuple(sorted((pi[u], pi[v])))] for (u, v) in M]
            return PM_EDGES.index(sorted([EDGES[i] for i in rel]))
        key = (tuple(sorted(relabel_pm(m) for m in P0)),
               tuple(sorted(relabel_pm(m) for m in P1)),
               tuple(sorted(relabel_pm(m) for m in P2)))
        if best is None or key < best:
            best = key
    return best

def run_t111(with_absent=True, chunk=200000, max_survivors_report=20):
    t0 = time.time()
    # ordered triples of distinct PMs
    nPM = len(PMS)
    seen = set()
    reps = []
    for m0 in range(nPM):
        for m1 in range(nPM):
            if m1 == m0: continue
            for m2 in range(nPM):
                if m2 == m0 or m2 == m1: continue
                # conflict check: edge-disjoint
                e0 = set(PM_EDGES[m0]); e1 = set(PM_EDGES[m1]); e2 = set(PM_EDGES[m2])
                if e0 & e1 or e0 & e2 or e1 & e2: continue
                key = canonical_triple([m0], [m1], [m2])
                if key in seen: continue
                seen.add(key)
                reps.append((m0, m1, m2))
    print(f"t111: {len(reps)} canonical triple reps", flush=True)
    n_feasible = 0; n_surv = 0; n_rows = 0
    results = []
    for rep_i, (m0, m1, m2) in enumerate(reps):
        forced = set(PM_EDGES[m0]) | set(PM_EDGES[m1]) | set(PM_EDGES[m2])
        free = [ei for ei, e in enumerate(EDGES) if e not in forced]
        F = len(free)
        nopt = 10 if with_absent else 9
        total = nopt ** F
        pm_class = np.full(15, -1, dtype=np.int64)
        pm_class[m0] = 0; pm_class[m1] = 1; pm_class[m2] = 2
        for start in range(0, total, chunk):
            rows = np.arange(start, min(start + chunk, total), dtype=np.int64)
            assign = np.zeros((len(rows), 15), dtype=np.int64)
            for j, ei in enumerate(free):
                assign[:, ei] = (rows // (nopt ** j)) % nopt
            # forced edges: mono option index for their color class (0,4,8)
            for i, m in enumerate([m0, m1, m2]):
                for e in PM_EDGES[m]:
                    assign[:, EDGES.index(e)] = 4 * i
            codes = ivc_codes_batch(assign)
            ok = np.ones(len(rows), dtype=bool)
            for i in range(3):
                ok &= (codes == MONO_CODE[i]).any(axis=1)
            ok &= l3_and_g_filter(codes, pm_class)
            idx = np.where(ok)[0]
            n_rows += len(rows)
            for j in idx:
                coloring = {}
                for ei, e in enumerate(EDGES):
                    if ei in free:
                        o = int(assign[j, ei])
                        coloring[e] = OPTS[o] if o != 9 else ABSENT
                    else:
                        # forced mono colors
                        for i, m in enumerate([m0, m1, m2]):
                            if e in PM_EDGES[m]:
                                coloring[e] = (i, i)
                verdict, info = decide(coloring)
                n_surv += 1
                if verdict == "FEASIBLE":
                    n_feasible += 1
                    print("*** WITNESS ***", flush=True)
                    print("triple:", [PM_EDGES[m] for m in (m0, m1, m2)], flush=True)
                    print("coloring:", coloring, flush=True)
                    print("info:", {kk: vv for kk, vv in info.items() if kk != "S"}, flush=True)
                    results.append({"triple": [PM_EDGES[m] for m in (m0, m1, m2)],
                                    "coloring": {str(k): v for k, v in coloring.items()},
                                    "witness": [str(w) for w in info["witness"]]})
                elif verdict == "UNRESOLVED":
                    print("t111 UNRESOLVED:", coloring, {kk: vv for kk, vv in info.items() if kk != "S"}, flush=True)
        print(f"rep {rep_i}/{len(reps)} done rows={n_rows} surv={n_surv} feas={n_feasible} t={time.time()-t0:.0f}s", flush=True)
    print(f"t111 done: rows={n_rows} survivors={n_surv} feasible={n_feasible} t={time.time()-t0:.0f}s")
    if results:
        with open("t111_witnesses.json", "w") as f:
            json.dump(results, f, indent=2)
    return results

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "mono"
    if mode == "mono":
        max_rows = int(sys.argv[2]) if len(sys.argv) > 2 else None
        run_mono(max_rows=max_rows)
    elif mode == "t111":
        run_t111()
