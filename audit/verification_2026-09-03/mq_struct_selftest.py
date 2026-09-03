"""
mq_struct_selftest.py -- brute-force equivalence tests for the pysat
structural encoding (mq_struct.StructSolver) on small frozen configurations.

Independent structural check (straight Python, no pysat): a slot coloring
passes iff
  (b) no PM instance other than the class's three forced mono ones has a
      monochrome IVC;
  (c) every realized non-mono IVC code has >= 2 PM instances.
The brute-force enumerator ranges over ALL slot colorings of the variable
free pairs (46 options per pair at K=2: absent, 9 single slots, 36 distinct
pairs).  All other pairs are pinned.
"""
import itertools, random, sys
from mq_basics import EDGES, SHAPE_PAIRS, pm_instances, MONO_DIGITS
from mq_struct import StructSolver

OPTS9 = [(a, b) for a in range(3) for b in range(3)]
MONO_CODES = set(sum(i * 3**x for x in range(6)) for i in range(3))

def brute_pass(slot_coloring, mono_shapes):
    # P1: present slots on a pair carry pairwise distinct color pairs
    for e, lst in slot_coloring.items():
        if len(set(lst)) != len(lst):
            return False
    insts = pm_instances(slot_coloring)
    def pure(t):
        for i, m in enumerate(mono_shapes):
            if t["shape"] == m:
                if all(slot_coloring[e][j] == (i, i) for (e, j) in t["edges"]):
                    return i
        return None
    codes = {}
    for t in insts:
        codes.setdefault(t["code"], []).append(t)
    mono_present = 0
    for c, members in codes.items():
        if c in MONO_CODES:
            pures = set()
            for t in members:
                pi = pure(t)
                if pi is None:
                    return False
                pures.add(pi)
            mono_present += len(pures)
        else:
            if len(members) < 2:
                return False
    return mono_present == 3

def gen_colorings(variable_pairs):
    opts = [()]
    for (a, b) in OPTS9:
        opts.append(((a, b),))
    for ((a1, b1), (a2, b2)) in itertools.combinations(OPTS9, 2):
        opts.append(((a1, b1), (a2, b2)))
    assert len(opts) == 46
    for combo in itertools.product(opts, repeat=len(variable_pairs)):
        yield dict(zip(variable_pairs, combo))

def run_test(mono_shapes, variable_pairs, rng, ntests, K=2):
    m0, m1, m2 = mono_shapes
    forced_pairs = {e for m in mono_shapes for e in SHAPE_PAIRS[m]}
    forced_of = {e: i for i, m in enumerate(mono_shapes) for e in SHAPE_PAIRS[m]}
    for test in range(ntests):
        sol = StructSolver(K, m0, m1, m2)
        pin = {}
        pinned_coloring = {}   # slot coloring of all non-variable pairs
        for e in EDGES:
            if e in variable_pairs:
                continue
            entries = sol.pair_slots[e]
            if e in forced_of:
                # exactly the forced (i,i) slot: all extra slots absent
                pin[e] = ['keep' if fcc is not None else None
                          for (fcc, k) in entries]
                pinned_coloring[e] = ((forced_of[e], forced_of[e]),)
            else:
                # free pair: random: absent or a single random slot
                if rng.random() < 0.5:
                    pin[e] = [None] * len(entries)
                    pinned_coloring[e] = ()
                else:
                    c = rng.choice(OPTS9)
                    pin[e] = [(c) if fcc is None else 'keep'
                              for (fcc, k) in entries]
                    pinned_coloring[e] = (c,)
        # make sure only the first non-forced slot position is used for a single
        for e, lst in pin.items():
            if e in forced_of:
                continue
            if lst and any(x is not None for x in lst):
                # exactly one slot present: put it at the first non-forced position
                first = min(pos for pos, (fcc, k) in enumerate(sol.pair_slots[e])
                            if fcc is None)
                spec = next((x for x in lst if x is not None), None)
                pin[e] = ['keep' if fcc is not None else None
                          for (fcc, k) in sol.pair_slots[e]]
                pin[e][first] = spec
        sol.pin_slots(pin)
        sol.build()
        sat, model = sol.solve()
        # brute
        base = dict(pinned_coloring)
        any_pass = False
        cnt = 0
        for sc_extra in gen_colorings(variable_pairs):
            cnt += 1
            full = dict(base)
            full.update(sc_extra)
            if brute_pass(full, mono_shapes):
                any_pass = True
                break
        assert cnt == 46 ** len(variable_pairs)
        if sat != any_pass:
            print("MISMATCH: sat", sat, "brute", any_pass)
            print("variable:", variable_pairs, "pinned:", pinned_coloring)
            if sat:
                sc = sol.model_to_slot_coloring(model)
                print("model:", {str(k): v for k, v in sc.items()})
                print("model brute:", brute_pass(sc, mono_shapes))
                for e, lst in pin.items():
                    if any(x is not None and x != 'keep' for x in lst):
                        print("pin of", e, lst)
            return False
        if test % 2 == 0:
            print(f"  test {test+1}/{ntests} ok (sat={sat})", flush=True)
    return True

if __name__ == "__main__":
    mono = (0, 4, 8)
    forced3 = set()
    for m in mono:
        forced3 |= set(SHAPE_PAIRS[m])
    free_pairs = [e for e in EDGES if e not in forced3]
    print("free pairs:", free_pairs, flush=True)
    rng = random.Random(20260903)
    ok1 = run_test(mono, [free_pairs[0]], rng, 8)
    print("test1 (1 variable free pair, K=2) ->", ok1, flush=True)
    if ok1:
        ok2 = run_test(mono, [free_pairs[0], free_pairs[1]], rng, 3)
        print("test2 (2 variable free pairs, K=2) ->", ok2, flush=True)
    if ok1 and ok2:
        ok3 = run_test(mono, [free_pairs[0]], rng, 8, K=3)
        print("test3 (1 variable free pair, K=3) ->", ok3, flush=True)
