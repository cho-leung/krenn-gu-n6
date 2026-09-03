"""
struct_anneal.py -- simulated annealing over P1-clean K=2 slot colorings
with mono class (0,4,8), seeking a configuration satisfying (b) no-new-mono
and (c) L3 (no singleton mixed IVC code).  Finding such a configuration
shows all-pairs K=2 SAT (a model).  Not finding one proves nothing.
"""
import random, time
from mq_basics import SHAPE_PAIRS, MONO_CODE, pm_instances, EDGES

MONO = (0, 4, 8)
COLORS = [(a, b) for a in range(3) for b in range(3)]
FORCED = {e: i for i, m in enumerate(MONO) for e in SHAPE_PAIRS[m]}
BASE = {e: ((FORCED[e], FORCED[e]),) for e in FORCED}

def cost(sc):
    insts = pm_instances(sc)
    counts = {}
    mono_bad = 0
    mono_present = [0, 0, 0]
    for t in insts:
        counts[t["code"]] = counts.get(t["code"], 0) + 1
        if t["code"] in MONO_CODE:
            i = MONO_CODE.index(t["code"])
            mono_present[i] += 1
            if t["shape"] != MONO[i] or mono_present[i] > 1:
                mono_bad += 1
    sing = sum(1 for c, n in counts.items() if n == 1 and c not in MONO_CODE)
    cover = sum(1 for m in mono_present if m == 0)
    return sing + 100 * mono_bad + 100 * cover, sing, mono_bad, cover

def random_move(sc, rng):
    sc = dict(sc)
    e = rng.choice(EDGES)
    cur = list(sc.get(e, ()))
    base_forced = e in FORCED
    if e not in sc and rng.random() < 0.5:
        return sc
    opts_add = [c for c in COLORS
                if c not in cur and not (base_forced and c == (FORCED[e], FORCED[e]))
                and len(cur) < 2]
    acts = []
    if len(cur) > 0 and not (base_forced and len(cur) == 1
                             and cur[0] == (FORCED[e], FORCED[e])):
        acts.append("del")
    acts.append("add")
    if not opts_add:
        acts.remove("add")
    if not acts:
        return sc
    act = rng.choice(acts)
    if act == "del":
        j = rng.randrange(len(cur))
        cur.pop(j)
    else:
        c = rng.choice(opts_add)
        cur.append(c)
    if cur:
        sc[e] = tuple(sorted(cur))
    else:
        sc.pop(e, None)
    return sc

def anneal(seconds=120, seed=1):
    rng = random.Random(seed)
    best = None
    t0 = time.time()
    attempts = 0
    while time.time() - t0 < seconds:
        attempts += 1
        sc = dict(BASE)
        T = 3.0
        c0, s0, b0, v0 = cost(sc)
        cur = sc
        cc = c0
        for step in range(4000):
            if time.time() - t0 > seconds:
                break
            nxt = random_move(cur, rng)
            c1, s1, b1, v1 = cost(nxt)
            if c1 < cc or rng.random() < 2.0 ** (-(c1 - cc) / T):
                cur, cc = nxt, c1
            T *= 0.998
            if cc == 0:
                return cur, cc, attempts
        if best is None or cc < best[1]:
            best = (cur, cc)
    return (best[0], best[1], attempts) if best else (None, None, attempts)

if __name__ == "__main__":
    import sys
    secs = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    sc, c, attempts = anneal(seconds=secs)
    print("annealing attempts:", attempts, "final cost:", c)
    if sc is not None and c == 0:
        print("CLEAN CONFIG FOUND:")
        for e in sorted(sc, key=str):
            print("   ", e, sc[e])
    else:
        print("no clean config found (informational only)")
