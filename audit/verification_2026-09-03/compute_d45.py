"""
D=4 / D=5 color generalization of the (6,3) simple-case enumeration.

Fresh implementation (no import of computation/*.py logic). IVC codes are
TUPLES (base-3 integer codes collide when digits reach 3+).

For D colors: classes (P0,...,P_{D-1}) of nonempty pairwise edge-disjoint
PM subsets; free edges carry D^2 color pairs + absent. Conditions:
  (b) no PM outside its class realizes a monochrome IVC of any color,
  (c) L3: every realized non-mono IVC tuple has >= 2 PMs.
Survivors (if any) go to an exact decision engine (tuple-based).
"""
import itertools, pickle, time, sys
import numpy as np
import sympy as sp
from collections import Counter
sys.path.insert(0, "/Users/junhaoliang/Projects/Krenn-Gu/computation")
from k6_basics import EDGES, PM_EDGES, EIDX   # data only

V = list(range(6))
PM_MASK = []
for M in PM_EDGES:
    m = 0
    for e in M:
        m |= 1 << EIDX[e]
    PM_MASK.append(m)

def enumerate_classes(D):
    """All ordered D-tuples of nonempty pairwise edge-disjoint PM subsets."""
    n = 15
    out = []
    def rec(k, used_mask, cur):
        if k == D:
            out.append(tuple(cur))
            return
        avail = [a for a in range(n) if not (PM_MASK[a] & used_mask)]
        for s in range(1, 1 << len(avail)):
            P = tuple(avail[j] for j in range(len(avail)) if s >> j & 1)
            E = used_mask
            for a in P:
                E |= PM_MASK[a]
            rec(k + 1, E, cur + [P])
    rec(0, 0, [])
    return out

def canonicalize(raw, D, maxs=None):
    """Min over the 720 S_6 perms of the lexicographic key (colors fixed).
    Vectorized over perms x raws, chunked.  `maxs` fixes the class-padding
    width so keys stay comparable across calls."""
    perms = list(itertools.permutations(range(6)))
    edge_inv = {e: i for i, e in enumerate(EDGES)}
    pm_lookup = {tuple(EIDX[e] for e in M): m for m, M in enumerate(PM_EDGES)}
    pm_relabel = np.zeros((len(perms), 15), dtype=np.int64)
    for pi_idx, pi in enumerate(perms):
        for m in range(15):
            rel = [edge_inv[tuple(sorted((pi[u], pi[v])))] for (u, v) in PM_EDGES[m]]
            pm_relabel[pi_idx, m] = pm_lookup[tuple(sorted(rel))]
    if maxs is None:
        maxs = max(len(P) for t in raw for P in t)
    T = -np.ones((len(raw), D, maxs), dtype=np.int64)
    for t, tup in enumerate(raw):
        for i, P in enumerate(tup):
            T[t, i, :len(P)] = sorted(P)
    seen = set()
    reps = []
    CH = 200
    for start in range(0, len(raw), CH):
        Tc = T[start:start + CH]
        rel = np.empty((len(perms), Tc.shape[0], D, maxs), dtype=np.int64)
        for i in range(D):
            cls = Tc[:, i, :]
            mask = cls >= 0
            idx = np.where(mask, cls, 0)
            rel[:, :, i, :] = np.where(mask[None, :, :], pm_relabel[:, idx], -1)
        rel = np.sort(rel, axis=-1)
        keys = rel.reshape(len(perms), Tc.shape[0], -1)
        for j in range(Tc.shape[0]):
            order = np.lexsort(keys[:, j, :].T[::-1])
            bkey = tuple(keys[order[0], j, :].tolist())
            if bkey not in seen:
                seen.add(bkey)
                reps.append(raw[start + j])
    return reps, seen

def run(D):
    t0 = time.time()
    raw = enumerate_classes(D)
    print(f"[D={D}] raw classes: {len(raw)} ({time.time()-t0:.0f}s)", flush=True)
    reps, seen = canonicalize(raw, D)
    print(f"[D={D}] orbit reps: {len(reps)} ({time.time()-t0:.0f}s)", flush=True)
    # completeness check: every raw class's canonical key is among the reps
    missing = sum(1 for t in raw if _canon_key(t, D) not in seen) if False else None
    with open(f"d{D}_raw.pkl", "wb") as f:
        pickle.dump(raw, f)
    with open(f"d{D}_reps.pkl", "wb") as f:
        pickle.dump(reps, f)

    # ---- batch ----
    nopt = D * D + 1          # D^2 pairs + absent
    MONO = [(i,) * 6 for i in range(D)]
    total_rows = 0
    survivors = []
    t1 = time.time()
    for rep_idx, classes in enumerate(reps):
        forced = set()
        for i, P in enumerate(classes):
            for m in P:
                for e in PM_EDGES[m]:
                    forced.add((e, i))          # edge e forced to mono color i
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
                assign[:, EIDX[e]] = i * D + i    # option (i,i) = i*D+i
            # per-row structural check (pure python, small batches)
            for r in range(len(rows)):
                row = assign[r]
                ok = _struct_ok(row, pm_class, D, nopt, MONO)
                if ok:
                    survivors.append((classes, row.tolist()))
        if rep_idx % 50 == 0:
            print(f"[D={D}] rep {rep_idx}/{len(reps)} rows={total_rows} surv={len(survivors)} ({time.time()-t1:.0f}s)", flush=True)
    print(f"[D={D}] BATCH DONE: total_rows={total_rows} survivors={len(survivors)} ({time.time()-t1:.0f}s)", flush=True)
    with open(f"d{D}_survivors.pkl", "wb") as f:
        pickle.dump(survivors, f)
    return raw, reps, survivors, total_rows

def _struct_ok(row, pm_class, D, nopt, MONO):
    """(b) no-new-mono + (c) L3, per row. IVC as tuple."""
    codes = []
    for M in PM_EDGES:
        ivc = [None] * 6
        dead = False
        for (u, v) in M:
            o = int(row[EIDX[(u, v)]])
            if o == nopt - 1:
                dead = True
                break
            a, b = o // D, o % D
            ivc[u] = a; ivc[v] = b
        codes.append(None if dead else tuple(ivc))
    # (b)
    for m in range(15):
        c = codes[m]
        if c is None:
            continue
        for i in range(D):
            if pm_class[m] != i and c == MONO[i]:
                return False
    # (c)
    cnt = Counter(c for c in codes if c is not None and c not in MONO)
    return all(v >= 2 for v in cnt.values())

if __name__ == "__main__":
    D = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    run(D)
