"""
struct_dfs.py -- guided depth-first search for a P1-clean structural
configuration with mono class (0,4,8) (exactly one mono PM per color),
K slots per pair, satisfying (b) no-new-mono and (c) L3.

State = dict pair -> tuple of present ordered color pairs (P1-clean).
Start = the 9 forced pairs with their (i,i) slot.  Expansion: add one slot
(pair, color) with capacity, P1-distinct, not the forced color of a forced
pair, and such that at least one NEW PM instance it creates has an IVC code
that is already realized in the current state (the "helps a group" gate).
(b) violations prune a state.  Success: no realized mixed code is a
singleton.  The gate makes the search incomplete as a decision procedure
(no UNSAT claims may be drawn) but focused for finding models.
"""
import sys, itertools, time
from mq_basics import SHAPE_PAIRS, MONO_DIGITS, MONO_CODE, pm_instances

MONO = (0, 4, 8)
COLORS = [(a, b) for a in range(3) for b in range(3)]
FORCED = {e: i for i, m in enumerate(MONO) for e in SHAPE_PAIRS[m]}

# shapes through each pair (other two pairs listed)
SHAPES_E = {}
for si, sh in enumerate(SHAPE_PAIRS):
    for e in sh:
        SHAPES_E.setdefault(e, []).append(si)

def code_of(digits):
    return sum(d * 3 ** x for x, d in enumerate(digits))

def analyze(sc):
    """instances; returns (codes: code->count, mono_violation: bool,
    singletons: set of mixed singleton codes, mono_present)."""
    insts = pm_instances(sc)
    counts = {}
    mono_ok = True
    for t in insts:
        counts[t["code"]] = counts.get(t["code"], 0) + 1
    mono_present = [0, 0, 0]
    for t in insts:
        if t["code"] in MONO_CODE:
            i = MONO_CODE.index(t["code"])
            mono_present[i] += 1
            if t["shape"] != MONO[i] or mono_present[i] > 1:
                mono_ok = False
    singletons = set(c for c, n in counts.items()
                     if n == 1 and c not in MONO_CODE)
    return counts, mono_ok, singletons, tuple(mono_present)

def main(K=2, time_budget=1500):
    start = {e: ((FORCED[e], FORCED[e]),) for e in FORCED}
    visited = set()
    stack = [start]
    states = 0
    found = None
    t0 = time.time()
    while stack:
        if time.time() - t0 > time_budget:
            print("time budget exhausted")
            break
        sc = stack.pop()
        key = frozenset((e, v) for e, lst in sc.items() for v in lst)
        if key in visited:
            continue
        visited.add(key)
        states += 1
        if states % 10000 == 0:
            print(f"... {states} states, stack {len(stack)}, slots "
                  f"{sum(len(v) for v in sc.values())}, "
                  f"{time.time()-t0:.0f}s", flush=True)
        counts, mono_ok, singletons, mono_present = analyze(sc)
        if not mono_ok:
            continue
        if any(mp == 0 for mp in mono_present):
            continue
        if not singletons:
            found = sc
            break
        # expansion candidates
        for e, cur in list(sc.items()) + [(e, ()) for e in set(SHAPES_E)
                                          if e not in sc]:
            if len(cur) >= K:
                continue
            used = set(cur)
            if e in FORCED:
                used.add((FORCED[e], FORCED[e]))
            shapes_e = SHAPES_E[e]
            for c in COLORS:
                if c in used:
                    continue
                # would a new instance through (e,c) hit a realized code?
                helps = False
                bad_mono = False
                for si in shapes_e:
                    others = [p for p in SHAPE_PAIRS[si] if p != e]
                    if any(o not in sc or len(sc[o]) == 0 for o in others):
                        continue
                    for combo in itertools.product(*(sc[o] for o in others)):
                        digits = [None] * 6
                        pos = dict(zip(others, combo))
                        pos[e] = c
                        for p, cc in pos.items():
                            digits[p[0]] = cc[0]
                            digits[p[1]] = cc[1]
                        code = code_of(digits)
                        if code in MONO_CODE:
                            # mono created outside the forced shape?
                            mono_i = MONO_CODE.index(code)
                            if si != MONO[mono_i]:
                                bad_mono = True
                        elif counts.get(code, 0) >= 1:
                            helps = True
                if bad_mono:
                    continue
                if not helps:
                    continue
                sc2 = dict(sc)
                sc2[e] = tuple(sorted(cur + (c,)))
                stack.append(sc2)
    print("states visited:", states)
    if found:
        print("FOUND config:")
        for e in sorted(found, key=str):
            print("   ", e, found[e])
        return found
    print("no config found (incomplete search -- no UNSAT claim)")
    return None

if __name__ == "__main__":
    main()
