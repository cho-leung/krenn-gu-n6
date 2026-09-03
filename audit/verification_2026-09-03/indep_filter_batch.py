"""
INDEPENDENT batch re-run for the (6,3) audit (2026-09-03).

Claims under audit:
  - for each of the 24 canonical classes, enumerating ALL free-edge
    assignments (9 color pairs + absent) and applying the no-new-mono +
    L3 conditions yields ZERO survivors.
  - total enumerated rows (as per the cached reps) — compare with the
    2,032,554 figure recorded in research_os/RESEARCH_STATE.md.

Implementation is fresh (no import of computation/*.py logic): own digit
expansion, own IVC code computation, own filter (both a naive per-row
version used for cross-checking the vectorized version, and the vectorized
version used for the full run).
"""
import pickle, sys, time
import numpy as np
from collections import Counter
sys.path.insert(0, "/Users/junhaoliang/Projects/Krenn-Gu/computation")
from k6_basics import EDGES, PM_EDGES, EIDX   # data only

OPTS = [(a, b) for a in range(3) for b in range(3)]          # option 0..8
MONO = [sum(i * 3**v for v in range(6)) for i in range(3)]   # 0, 364, 728
MONO_SET = set(MONO)

def ivc_codes(assign):
    """(N,15) option indices -> (N,15) IVC codes, -1 = dead PM. Own implementation."""
    N = assign.shape[0]
    codes = np.zeros((N, 15), dtype=np.int64)
    for mi, M in enumerate(PM_EDGES):
        acc = np.zeros(N, dtype=np.int64)
        dead = np.zeros(N, dtype=bool)
        for (u, v) in M:
            ei = EIDX[(u, v)]
            o = assign[:, ei]
            a = o // 3      # first color of option (a,b): o = 3a+b -> a = o//3
            b = o % 3
            acc += a * 3**u + b * 3**v
            dead |= (o == 9)
        codes[:, mi] = acc
        codes[dead, mi] = -1
    return codes

def filter_naive(codes_row, pm_class):
    """Per-row reference filter: no-new-mono + L3. Returns bool."""
    seen = Counter()
    for m, c in enumerate(codes_row):
        if c == -1:
            continue
        if c in MONO_SET:
            if pm_class[m] == -1 or MONO[pm_class[m]] != c:
                return False   # a PM outside its mono class has a mono IVC
        else:
            seen[c] += 1
    return all(v >= 2 for v in seen.values())

def filter_vec(codes, pm_class):
    """Vectorized version (own implementation, sort+diff style)."""
    N = codes.shape[0]
    keep = np.ones(N, dtype=bool)
    # no-new-mono
    for i in range(3):
        bad = ((pm_class[None, :] != i) & (codes == MONO[i])).any(axis=1)
        keep &= ~bad
    # L3 via sorting
    c = codes.astype(np.int64).copy()
    c[c == -1] = 10**18
    for mc in MONO:
        c[c == mc] = 10**18
    s = np.sort(c, axis=1)
    left = np.ones_like(s, dtype=bool); left[:, 1:] = s[:, 1:] != s[:, :-1]
    right = np.ones_like(s, dtype=bool); right[:, :-1] = s[:, 1:] != s[:, :-1]
    sing = (s != 10**18) & left & right
    keep &= ~sing.any(axis=1)
    return keep

# ---- cross-check vectorized vs naive on random inputs -----------------------
rng = np.random.default_rng(12345)
X = rng.integers(0, 10, size=(20000, 15))
pc = rng.integers(-1, 3, size=15)
pc_ok = filter_vec(X, pc)
naive = np.array([filter_naive(X[j], pc) for j in range(20000)])
assert (pc_ok == naive).all(), "vectorized filter disagrees with naive!"
print("filter cross-check OK (20,000 random rows, vectorized == naive)")

# ---- full batch over the 24 cached classes -----------------------------------
with open("/Users/junhaoliang/Projects/Krenn-Gu/computation/triples_cache.pkl", "rb") as f:
    reps = pickle.load(f)

t0 = time.time()
total_rows = 0
survivors = 0
by_size = Counter()
for P0, P1, P2 in reps:
    forced = set()
    for P in (P0, P1, P2):
        for m in P:
            forced |= set(PM_EDGES[m])
    free = [EIDX[e] for e in EDGES if e not in forced]
    F = len(free)
    by_size[(len(P0), len(P1), len(P2))] += 1
    total_rows += 10 ** F
    pm_class = np.full(15, -1, dtype=np.int64)
    for i, P in enumerate([P0, P1, P2]):
        for m in P:
            pm_class[m] = i
    chunk = 200000
    for start in range(0, 10 ** F, chunk):
        rows = np.arange(start, min(start + chunk, 10 ** F), dtype=np.int64)
        assign = np.zeros((len(rows), 15), dtype=np.int64)
        for j, ei in enumerate(free):
            assign[:, ei] = (rows // (10 ** j)) % 10
        for i, P in enumerate([P0, P1, P2]):
            for m in P:
                for e in PM_EDGES[m]:
                    assign[:, EIDX[e]] = 3 * i + i   # option (i,i) = 3i+i
        codes = ivc_codes(assign)
        ok = filter_vec(codes, pm_class)
        survivors += int(ok.sum())
print(f"batch done: total_rows={total_rows} survivors={survivors} "
      f"size_classes={dict(by_size)} t={time.time()-t0:.1f}s")
print("recorded figure in RESEARCH_STATE.md: 2,032,554")
if survivors == 0:
    print("BATCH OK: zero survivors across all", total_rows, "enumerated rows")
else:
    print("BATCH FAIL: survivors found:", survivors)
    sys.exit(1)
