"""
Cross-check THEIR current filter implementations (computation/run_search.py)
against an independent naive reference, on random inputs including
mono-only colorings. (2026-09-03 audit)
"""
import sys
import numpy as np
from collections import Counter
sys.path.insert(0, "/Users/junhaoliang/Projects/Krenn-Gu/computation")
from run_search import ivc_codes_batch, l3_group_filter, l3_and_g_filter
from k6_basics import PM_EDGES, EIDX

MONO = [0, 364, 728]
MONO_SET = set(MONO)

def filter_naive(codes_row, pm_class):
    seen = Counter()
    for m, c in enumerate(codes_row):
        if c == -1:
            continue
        if c in MONO_SET:
            if pm_class[m] == -1 or MONO[pm_class[m]] != c:
                return False
        else:
            seen[c] += 1
    return all(v >= 2 for v in seen.values())

rng = np.random.default_rng(999)

# --- test 1: full random (options 0..9), l3_and_g_filter ---------------------
X = rng.integers(0, 10, size=(30000, 15))
pc = rng.integers(-1, 3, size=15)
codes = ivc_codes_batch(X)
their = l3_and_g_filter(codes, pc)
naive = np.array([filter_naive(codes[j], pc) for j in range(30000)])
print("test1 (full random, l3_and_g_filter): match =", bool((their == naive).all()),
      " theirs_pass =", int(their.sum()), " naive_pass =", int(naive.sum()))
if not (their == naive).all():
    j = np.where(their != naive)[0][0]
    print("first mismatch row:", X[j], "codes:", codes[j], "theirs:", their[j], "naive:", naive[j])
    sys.exit(1)

# --- test 2: mono-only colorings, l3_group_filter ----------------------------
X2 = rng.integers(0, 3, size=(30000, 15)) * 4
codes2 = ivc_codes_batch(X2)
their2 = l3_group_filter(codes2)
# naive L3-only reference (no class condition)
def l3_naive(codes_row):
    seen = Counter(c for c in codes_row if c != -1 and c not in MONO_SET)
    return all(v >= 2 for v in seen.values())
naive2 = np.array([l3_naive(codes2[j]) for j in range(30000)])
print("test2 (mono-only, l3_group_filter): match =", bool((their2 == naive2).all()),
      " theirs_pass =", int(their2.sum()), " naive_pass =", int(naive2.sum()))
if not (their2 == naive2).all():
    j = np.where(their2 != naive2)[0][0]
    print("first mismatch row:", X2[j], "codes:", codes2[j])
    sys.exit(1)

print("THEIR CURRENT FILTERS: CROSS-CHECK OK")
