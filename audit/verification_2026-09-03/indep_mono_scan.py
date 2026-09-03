"""
INDEPENDENT mono-edge scan re-run for the (6,3) audit (2026-09-03).

Audits the mono-validation claim and resolves the doc discrepancy
(248,310 vs 211,590). Phases:
  1. enumerate all 3^15 mono colorings with MY OWN filter:
       count_a   = pass "all three mono IVCs realized"
       count_al3 = pass count_a AND L3
  2. run computation/search_core.decide on every count_al3 survivor with
     FULL capture (verdict, reason, exceptions). Any FEASIBLE, UNRESOLVED,
     or ERROR aborts the audit with a counterexample dump.
Survivors are saved to mono_survivors.npz for the independent-engine
cross-check.
"""
import sys, time, json
import numpy as np
from collections import Counter
sys.path.insert(0, "/Users/junhaoliang/Projects/Krenn-Gu/computation")
from k6_basics import EDGES
from search_core import decide, OPTS, ABSENT

MONO = [0, 364, 728]
MONO_SET = set(MONO)

def ivc_codes(assign):
    N = assign.shape[0]
    codes = np.zeros((N, 15), dtype=np.int64)
    for mi, M in enumerate(PM_EDGES):
        acc = np.zeros(N, dtype=np.int64); dead = np.zeros(N, dtype=bool)
        for (u, v) in M:
            ei = EIDX[(u, v)]
            a = assign[:, ei] // 3; b = assign[:, ei] % 3
            acc += a * 3**u + b * 3**v
            dead |= (assign[:, ei] == 9)
        codes[:, mi] = acc; codes[dead, mi] = -1
    return codes

def l3_filter(codes):
    N = codes.shape[0]
    c = codes.astype(np.int64).copy()
    c[c == -1] = 10**18
    for mc in MONO:
        c[c == mc] = 10**18
    s = np.sort(c, axis=1)
    left = np.ones_like(s, dtype=bool); left[:, 1:] = s[:, 1:] != s[:, :-1]
    right = np.ones_like(s, dtype=bool); right[:, :-1] = s[:, 1:] != s[:, :-1]
    sing = (s != 10**18) & left & right
    return ~sing.any(axis=1)

from k6_basics import PM_EDGES, EIDX
t0 = time.time()
count_a = 0
surv_rows = []
CH = 500000
for start in range(0, 3**15, CH):
    rows = np.arange(start, min(start + CH, 3**15), dtype=np.int64)
    assign = np.zeros((len(rows), 15), dtype=np.int64)
    for ei in range(15):
        assign[:, ei] = (rows // (3**ei)) % 3
    assign = assign * 4          # mono options: (i,i) = option 4i
    codes = ivc_codes(assign)
    ok_a = np.ones(len(rows), dtype=bool)
    for i in range(3):
        ok_a &= (codes == MONO[i]).any(axis=1)
    count_a += int(ok_a.sum())
    ok = ok_a & l3_filter(codes)
    surv_rows.append(assign[ok])
print(f"phase1 done: count_a={count_a} count_a_l3={sum(len(s) for s in surv_rows)} t={time.time()-t0:.0f}s", flush=True)
surv = np.concatenate(surv_rows, axis=0)
np.savez_compressed("mono_survivors.npz", assign=surv)
print("survivors saved:", surv.shape, flush=True)

# ---- phase 2: decide() every survivor with full capture --------------------
import multiprocessing as mp
def worker(assign_row):
    coloring = {}
    for ei, e in enumerate(EDGES):
        o = int(assign_row[ei])
        coloring[e] = OPTS[o] if o != 9 else ABSENT
    try:
        v, info = decide(coloring)
        return (v, info.get("reason"), None)
    except Exception as ex:
        return ("ERROR", str(ex), assign_row.tolist())

nprocs = min(8, max(1, mp.cpu_count() - 2))
t1 = time.time()
verdicts = Counter(); reasons = Counter(); bad = []
with mp.Pool(nprocs) as pool:
    for i, (v, r, row) in enumerate(pool.imap_unordered(worker, surv, chunksize=256)):
        verdicts[v] += 1
        if v == "INFEASIBLE":
            reasons[r] += 1
        else:
            bad.append((v, r, row))
            print("BAD VERDICT:", v, r, row, flush=True)
        if (i + 1) % 50000 == 0:
            print(f"decide {i+1}/{len(surv)} {dict(verdicts)} t={time.time()-t1:.0f}s", flush=True)
print("phase2 done:", dict(verdicts), f"t={time.time()-t1:.0f}s", flush=True)
print("reasons:", dict(reasons), flush=True)
if bad or verdicts["FEASIBLE"] or verdicts["UNRESOLVED"] or verdicts["ERROR"]:
    print("MONO SCAN AUDIT FAILED — see above", flush=True)
    sys.exit(1)
print("MONO SCAN OK: all survivors INFEASIBLE with exact reasons", flush=True)
