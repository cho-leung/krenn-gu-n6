"""
mq_struct.py -- SAT (bit-blasted, pysat/Cadical) search for the STRUCTURAL
layer of the multigraph (6,3) question, for a FIXED (1,1,1)-mono class.

Mono class = three pairwise-pair-disjoint PM shapes (m0,m1,m2).  Each pair
of shape mi carries a permanently present (i,i) slot; the remaining pairs
are free.  Every pair may carry up to K slots; present slots on a pair must
carry pairwise DISTINCT ordered color pairs (Lemma P1).

Structural constraints (necessary for any all-nonzero-weight (6,3) solution
whose mono PM sets are exactly the three forced singleton PMs):
  (b) no-new-mono: no PM instance other than the three forced mono ones has
      a monochrome IVC;
  (c) L3: every present non-mono instance has a partner present instance
      with the SAME IVC (any realized non-mono IVC group has >= 2 members).

A SAT model yields a slot coloring (per pair the tuple of present ordered
color pairs) to feed to mq_decide.decide for the exact weight question.

Correctness of the CNF is tested against brute force on small frozen
configurations (see mq_struct_selftest()).
"""
import itertools
from pysat.formula import CNF
from pysat.solvers import Cadical153
from mq_basics import EDGES, EIDX, SHAPE_PAIRS

# color value <-> 2 bits: 0 -> (0,0), 1 -> (0,1), 2 -> (1,0); (1,1) invalid
BIT_OF = {0: (0, 0), 1: (0, 1), 2: (1, 0)}
VAL_OF = {(0, 0): 0, (0, 1): 1, (1, 0): 2}

class StructSolver:
    def __init__(self, K, m0, m1, m2, extra_on_forced=True, extra_on_free=True):
        """
        K slots max per pair.  m0,m1,m2 pairwise pair-disjoint shape indices.
        extra_on_forced: may forced pairs host extra (non-(i,i)) slots?
        extra_on_free:   may free pairs host up to K slots (else exactly 1)?
        """
        self.K = K
        self.mono_shapes = (m0, m1, m2)
        self.forced_col = {}
        for i, m in enumerate((m0, m1, m2)):
            for e in SHAPE_PAIRS[m]:
                assert e not in self.forced_col, "shapes must be pair-disjoint"
                self.forced_col[e] = i
        # slot lists: entry = (forced_color_or_None, local_index)
        self.pair_slots = {}
        for e in EDGES:
            if e in self.forced_col:
                self.pair_slots[e] = [(self.forced_col[e], 0)] + \
                    ([(None, k) for k in range(1, K)] if extra_on_forced else [])
            else:
                if extra_on_free:
                    self.pair_slots[e] = [(None, k) for k in range(K)]
                else:
                    self.pair_slots[e] = [(None, 0)]

        a = CNF()
        self.alloc = a
        cnf = a
        nvar = [0]
        def newv():
            nvar[0] += 1
            return nvar[0]
        def add(cl):
            cnf.append([int(x) for x in cl])

        # --- slot-level variables ---
        P = {}    # (e, k) -> presence lit (only non-forced slots)
        COL = {}  # (e, k) -> ((a1,a2),(b1,b2)) bits for non-forced slots
        for e in EDGES:
            for fc, k in self.pair_slots[e]:
                if fc is None:
                    p = newv(); P[(e, k)] = p
                    ca = (newv(), newv()); cb = (newv(), newv())
                    COL[(e, k)] = (ca, cb)
                    for (x, y) in (ca, cb):
                        add([-x, -y])       # (1,1) invalid
        self.P = P; self.COL = COL
        self.newv = newv; self.add = add

        def color_spec(e, k, side):
            """('c', value) or ('v', (bitlits))."""
            fc = dict(self.pair_slots[e])[k] if False else None
            for fcc, kk in self.pair_slots[e]:
                if kk == k:
                    fc = fcc
            if fc is not None:
                return ('c', fc)
            return ('v', COL[(e, k)][side])

        # --- per-pair slot distinctness (P1) ---
        for e in EDGES:
            entries = self.pair_slots[e]
            for j1 in range(len(entries)):
                for j2 in range(j1 + 1, len(entries)):
                    fc1, k1 = entries[j1]; fc2, k2 = entries[j2]
                    if fc1 is not None and fc2 is not None:
                        continue
                    a1 = color_spec(e, k1, 0); a2 = color_spec(e, k2, 0)
                    b1 = color_spec(e, k1, 1); b2 = color_spec(e, k2, 1)
                    cl = []
                    if fc1 is None: cl.append(-P[(e, k1)])
                    if fc2 is None: cl.append(-P[(e, k2)])
                    eA = self.eq_aux(a1, a2)
                    eB = self.eq_aux(b1, b2)
                    cl += [-eA, -eB]
                    add(cl)
        # --- instances ---
        instances = []
        for s, shape in enumerate(SHAPE_PAIRS):
            opts = [self.pair_slots[e] for e in shape]
            for combo in itertools.product(*opts):
                pres = []
                for e, (fc, k) in zip(shape, combo):
                    if fc is None:
                        pres.append(P[(e, k)])
                g = newv()
                for pl in pres:
                    add([-g, pl])           # g -> slot present
                add([g] + [-pl for pl in pres])   # all slots present -> g (unit if none)
                instances.append({"shape": s,
                                  "combo": tuple(k for _, k in combo),
                                  "fcs": tuple(fc for fc, _ in combo),
                                  "g": g})
        self.instances = instances
        self.color_spec = color_spec

        # per instance per vertex: color spec of the slot covering vertex x
        self.vertex_spec = []
        for t in instances:
            shape = SHAPE_PAIRS[t["shape"]]
            vs = [None] * 6
            for e, (fc, k) in zip(shape, zip(t["fcs"], t["combo"])):
                vs[e[0]] = color_spec(e, k, 0)
                vs[e[1]] = color_spec(e, k, 1)
            self.vertex_spec.append(vs)

    # ---------------- helpers ----------------
    def eq_aux(self, c1, c2):
        """lit: 'color values equal'."""
        if c1[0] == 'c' and c2[0] == 'c':
            return self.T() if c1[1] == c2[1] else self.F()
        if c1[0] == 'c':
            c1, c2 = c2, c1
        if c2[0] == 'c':
            # var == const: e <-> (bit1==w1 AND bit2==w2)
            bits = BIT_OF[c2[1]]
            e = self.newv()
            for (x, w) in zip(c1[1], bits):
                # e -> (x == w)
                if w == 1:
                    self.add([-e, x])
                else:
                    self.add([-e, -x])
            # (x1==w1 AND x2==w2) -> e:
            # clause e v (x1 != w1) v (x2 != w2)  (x!=w is -x for w=1, x for w=0)
            cl = [e]
            for (x, w) in zip(c1[1], bits):
                cl.append(-x if w == 1 else x)
            self.add(cl)
            return e
        # both var: e <-> bitwise equality of the two 2-bit pairs
        e = self.newv()
        (x1, x2), (y1, y2) = c1[1], c2[1]
        # e -> xi == yi for each bit
        for (x, y) in ((x1, y1), (x2, y2)):
            self.add([-e, -x, y]); self.add([-e, x, -y])
        # (x1==y1 AND x2==y2) -> e : forbid the four bad assignments
        self.add([e, x1, y1, x2, y2])
        self.add([e, x1, y1, -x2, -y2])
        self.add([e, -x1, -y1, x2, y2])
        self.add([e, -x1, -y1, -x2, -y2])
        return e

    def T(self):
        if not hasattr(self, '_T'):
            self._T = self.newv(); self.add([self._T])
        return self._T
    def F(self):
        if not hasattr(self, '_F'):
            self._F = self.newv(); self.add([-self._F])
        return self._F

    def color_is(self, c, i):
        """lit: 'color == i' (both bits match the constant)."""
        if c[0] == 'c':
            return self.T() if c[1] == i else self.F()
        bits, want = c[1], BIT_OF[i]
        e = self.newv()
        for (x, w) in zip(bits, want):
            # e -> (x == w)
            if w == 1:
                self.add([-e, x])
            else:
                self.add([-e, -x])
        # (x1==w1 AND x2==w2) -> e:
        # clause e v (x1 != w1) v (x2 != w2)  (x!=w is -x for w=1, x for w=0)
        cl = [e] + [-x if w == 1 else x for (x, w) in zip(bits, want)]
        self.add(cl)
        return e

    def is_pure_mono(self, t):
        """i if t is the forced mono instance of shape mi (all slots forced
        color i), else None."""
        if t["shape"] not in self.mono_shapes:
            return None
        i = self.mono_shapes.index(t["shape"])
        for fc in t["fcs"]:
            if fc != i:
                return None
        return i

    def build(self, no_mono=False, no_l3=False):
        """Add no-new-mono and L3 clauses.  Call after __init__.
        no_mono/no_l3 disable the respective constraint families (diagnostics)."""
        insts = self.instances
        vs = self.vertex_spec
        # no-new-mono: present & all-6-digits == i forbidden unless pure mono i
        if not no_mono:
            for t, vsp in zip(insts, vs):
                pure = self.is_pure_mono(t)
                for i in range(3):
                    if pure == i:
                        continue
                    lits = [self.color_is(c, i) for c in vsp]
                    self.add([-t["g"]] + [-l for l in lits])
        # L3 partner clauses
        self.pairs = []
        if no_l3:
            return
        for j1 in range(len(insts)):
            for j2 in range(j1 + 1, len(insts)):
                t1, t2 = insts[j1], insts[j2]
                if self.is_pure_mono(t1) is not None and self.is_pure_mono(t2) is not None:
                    continue
                # all 6 digits equal?
                eq_lits = []
                forced_diff = False
                for x in range(6):
                    c1, c2 = vs[j1][x], vs[j2][x]
                    if c1[0] == 'c' and c2[0] == 'c' and c1[1] != c2[1]:
                        forced_diff = True
                        break
                    eq_lits.append(self.eq_aux(c1, c2))
                if forced_diff:
                    continue
                h = self.newv()
                self.add([-h, t1["g"]])
                self.add([-h, t2["g"]])
                for l in eq_lits:
                    self.add([-h, l])
                self.add([h, -t1["g"], -t2["g"]] + [-l for l in eq_lits])
                self.pairs.append((j1, j2, h))
        for t in insts:
            if self.is_pure_mono(t) is not None:
                continue
            hs = [h for (j1, j2, h) in self.pairs if j1 is not None and
                  (self.instances[j1] is t or self.instances[j2] is t)]
            # hs nonempty always? if empty, instance can never have partner:
            # then L3 forces it absent: add [-g]
            if hs:
                self.add([-t["g"]] + hs)
            else:
                self.add([-t["g"]])

    # ---------------- solving ----------------
    def pin_slots(self, pin):
        """
        pin: dict pair -> list over the pair's slot positions (pair_slots order):
        None means slot absent, (a,b) means present with that color pair.
        Only valid for non-forced slots (forced slot position 0 of a forced
        pair is always (i,i); pin entries for it are ignored).
        """
        for e, entries in self.pair_slots.items():
            if e not in pin:
                continue
            for pos, (fc, k) in enumerate(entries):
                if fc is not None:
                    continue
                spec = pin[e][pos] if pos < len(pin[e]) else None
                if spec is None:
                    self.add([-self.P[(e, k)]])
                else:
                    a, b = spec
                    self.add([self.P[(e, k)]])
                    ca, cb = self.COL[(e, k)]
                    for bits, v in ((ca, a), (cb, b)):
                        w = BIT_OF[v]
                        for (x, y) in zip(bits, w):
                            if y == 1:
                                self.add([x])
                            else:
                                self.add([-x])

    def check_model(self, model, assumptions=()):
        """True iff model satisfies every CNF clause and assumption."""
        mv = {abs(l): (l > 0) for l in model}
        for cl in self.alloc.clauses:
            if not any((mv[abs(l)] if l > 0 else not mv[abs(l)]) for l in cl):
                return False
        for l in assumptions:
            if not (mv[abs(l)] if l > 0 else not mv[abs(l)]):
                return False
        return True

    def solve(self, assumptions=(), validate=True):
        cad = Cadical153(self.alloc)
        sat = cad.solve(assumptions=list(assumptions))
        model = cad.get_model() if sat else None
        cad.delete()
        if sat:
            if validate:
                assert self.check_model(model, assumptions), \
                    "SAT model violates the CNF (internal error)"
            return sat, model
        # UNSAT: double-check with an independent solver
        from pysat.solvers import Glucose4
        g = Glucose4(self.alloc)
        sat2 = g.solve(assumptions=list(assumptions))
        g.delete()
        assert not sat2, "Cadical UNSAT but Glucose4 finds a model"
        return sat, model

    def iter_models(self, max_models=10**6, assumptions=()):
        """Yield SAT models; blocks each found model."""
        cad = Cadical153(self.alloc)
        n = 0
        while n < max_models:
            sat = cad.solve(assumptions=list(assumptions))
            if not sat:
                break
            model = cad.get_model()
            yield model
            n += 1
            # block: at least one lit flips
            block = [-l for l in model]
            cad.add_clause(block)
        cad.delete()

    # ---------------- decode ----------------
    def model_colors(self, model):
        mv = {abs(l): (l > 0) for l in model}
        def rd(c):
            if c[0] == 'c':
                return c[1]
            b1, b2 = c[1]
            return VAL_OF[(1 if mv[b1] else 0, 1 if mv[b2] else 0)]
        return mv, rd

    def model_to_slot_coloring(self, model):
        mv, rd = self.model_colors(model)
        out = {}
        for e in EDGES:
            slots = []
            for fc, k in self.pair_slots[e]:
                if fc is not None:
                    slots.append((fc, fc))
                else:
                    if mv[self.P[(e, k)]]:
                        ca, cb = self.COL[(e, k)]
                        slots.append((rd(('v', ca)), rd(('v', cb))))
            out[e] = tuple(slots)
        return out
