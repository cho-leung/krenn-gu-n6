# Q1 attack (distinct-pair parallel-edge elimination) — 2026-09-03

Author: Claude (research assistant), Krenn–Gu project.  All claims are
labeled: PROVED / COMPUTATIONAL / CONJECTURAL / CLAIMED-UNVERIFIED.
COMPUTATION != PROOF; PRODUCED != AUDITED.  No existing project file was
modified; everything new lives in this file plus new scripts in
audit/verification_2026-09-03/ (mq_basics.py, mq_decide.py, mq_struct.py,
mq_struct_selftest.py, run_struct_engine.py).

## 1. The problem and the sharpened Q1 statement

Reference setup (see proof/parallel_edges.md, proof/formulation.md): the
(6,3) problem asks for a bi-colored weighted MULTIGRAPH on 6 vertices whose
inherited-vertex-coloring sums satisfy w(000)=w(111)=w(222)=1 and w(sigma)=0
for every other of the 729 colorings.  Parallel edges on a vertex pair are
allowed only with pairwise DISTINCT ordered color pairs (Lemma P1 [PROVED]:
equal-pair parallels merge by adding weights).  Per pair e={u,v} (u<v) a
slot is an edge with an ordered color pair (a,b) (a at u, b at v) and a
complex weight; a perfect-matching instance M = (shape, one slot per pair
of the shape); x_M = product of the slot weights along M.  R3/R4 [PROVED]:
a PM has mono IVC i iff all three slots carry (i,i); sum_{P_i} x_M = 1 for
each color i, and every realized non-mono IVC code group sums to 0 (L3
[PROVED]: realized non-mono codes have >= 2 member PMs when weights are
nonzero).  R5 [PROVED]: x in (C*)^#inst is realizable by slot weights iff
prod_M x_M^{c_M} = 1 for every c in ker U^T (U = instance-slot incidence).

Simple case (at most one edge per pair) is exhaustively UNSAT [COMPUTATIONAL,
audited 2026-09-03, certificate proof/certificate_simple63.md].  Hence:
a multigraph (6,3) solution exists iff it uses parallel edges on distinct
color pairs at some pair.

Q1 (as attacked here):  no multigraph (6,3) solution exists with exactly
three monochrome PMs, one of each color, i.e., with the mono class given by
three pair-disjoint shapes (m0,m1,m2), m_i carrying the unique (i,i) edge
per pair of shape m_i and no other (i,i) edges anywhere.

Sharpened note (why the restriction is a restriction, not WLOG):  deleting
zero-weight slots reduces any solution to an all-nonzero-weight solution on
a sub-multigraph with the same sums; so WLOG all present slot weights are
nonzero.  Under that reduction the mono sums force P_i nonempty, but |P_i| =
1 is NOT forced in general: a color's (i,i) edges may span several PMs.
Simple-case UNSAT is exhaustive over ALL |P_i|; the multigraph search below
only covers the |P_0|=|P_1|=|P_2|=1 layer with shapes (m0,m1,m2) = (0,4,8)
(the three PMs of the base graph H below).  Any claim about Q1 in full is
CONJECTURAL below this line unless explicitly proved.

## 2. Structural layer: what must a candidate look like?  [PROVED items]

Let the three mono shapes be 0,4,8 (SHAPE_PAIRS):  shape 0 = {(0,1),(2,3),
(4,5)} color 0; shape 4 = {(0,2),(1,4),(3,5)} color 1; shape 8 = {(0,3),
(1,5),(2,4)} color 2.  Their union is a 3-regular 6-vertex graph H with 9
edges (= the triangular prism on vertex sets {0,2,3} and {1,4,5} with
cross-edges (0,1),(2,4),(3,5)).

Lemma S1 [PROVED]: H has exactly four PMs: shapes 0, 4, 8 (the mono ones)
and shape 1 = {(0,1),(2,4),(3,5)}.  Shape 1's IVC on H is (0,0,2,1,2,1),
code 450; the three mono PMs have codes 000,111,222.
Proof: direct check of the 15 shapes of K_6 (done twice: by enumeration and
by hand; shape 1 uses one cross-edge and two in-triangle edges).

Corollary S2 [PROVED]: any structural configuration with mono class
(0,4,8) and no other (i,i) edges must realize code 450 in at least two PM
instances (L3), since the base instance {shape 1 on H} always exists and is
the unique code-450 PM unless extra slots at compatible pairs are added.
"Compatible" pairs for code 450 digits (0,0,2,1,2,1) require slot color
(d_u,d_v):  (0,1):(0,0) (forced); (0,2):(0,2); (0,3):(0,1); (0,4):(0,2);
(0,5):(0,1); (1,2):(0,2); (1,3):(0,1); (1,4):(0,2); (1,5):(0,1); (2,3):
(2,1); (2,4):(2,2) (forced); (2,5):(2,1); (3,4):(1,2); (3,5):(1,1) (forced);
(4,5):(2,1).

Note S3 [PROVED]: because extra slots on a pair must be distinct from the
pair's forced color (P1), no extra on (0,1),(2,4),(3,5) can carry (0,0),
(2,2),(1,1) respectively; hence code-450 partners use the pairs in S2 other
than the three forced-compatible ones.  E.g. the partner PM {(0,2):(0,2),
(1,4):(0,2),(3,5):(1,1)} = shape 4 with both extra slots; or {(0,4):(0,2),
(1,3):(0,1),(2,5):(2,1)} (three free pairs).  Every such addition creates
further PM instances (cascade); each realized mixed code must be paired
again.

## 3. Weight-layer decision procedure (new, exact over Q with C-numeric root find)

New scripts (self-contained; mirrors the audited simple-case pipeline of
computation/search_core.py generalized to slot colorings):
- mq_basics.py: slot-coloring -> PM instances (shape, combo, edges, IVC
  digits, base-3 code); EDGES/EIDX/SHAPE_PAIRS re-derived.
- mq_struct.py: pysat CNF for the structural layer at fixed mono class:
  per-pair slots (forced (i,i) slot on shape-m_i pairs; up to K slots per
  pair), P1 distinctness per pair (2-bit color encoding, domain clauses),
  no-new-mono and L3 (partner) constraints.  Model validated against its own
  CNF and double-checked by an independent solver; and the encoder's
  equivalence with brute force is tested on frozen configurations
  (mq_struct_selftest.py) including P1.
- mq_decide.py: exact decision for the weight layer of one slot coloring:
  group sums -> linear system A x = b over Q (mono rows rhs 1, non-mono
  group rows rhs 0), linsolve, affine space L of dim k; lift relations from
  ker U^T as polynomial equations on L; k=0/k=1 handled exactly
  (rational/root/gcd); k>=2 by numeric root search (univariate slicing for
  one polynomial in two parameters; damped complex Newton otherwise),
  60-digit mpmath polish, then FULL verification: lift x to slot weights
  (log x = U^T log w) and directly evaluate all 729 coloring sums at 60
  digits (verify_witness_full).  Verdicts FEASIBLE / INFEASIBLE /
  UNRESOLVED.

Bug found and fixed in mq_struct.py (2026-09-03):  the var-vs-const branch
of eq_aux and color_is encoded the "conjunction -> e" clause with inverted
bit literals ([e, -x1, -x2] for a 00 constant instead of [e, x1, x2]).
Effect: color-equality-to-a-constant could be FALSE while the colors were
equal, so P1 distinctness against forced (i,i) slots was NOT enforced and
no-new-mono/L3 clauses were under-constrained.  Consequences for earlier
claims:  (i) UNSAT claims survive (a weaker encoding proving UNSAT implies
UNSAT for the corrected encoding);  (ii) SAT claims and all structural
models previously reported are VOID and are re-derived below.  The self-test
suite now checks P1 in brute_pass as well; all self-tests pass on the
corrected encoder [COMPUTATIONAL].

## 4. Weight-layer caveat (zero-coordinate subtlety)  [PROVED]

Lemma W1 [PROVED]: A slot coloring C admits a (6,3) weight solution with
arbitrary complex weights iff some sub-coloring C' of C (delete a subset of
slots) admits a solution with all weights nonzero.
Proof: delete the zero-weight slots; PMs through them contributed 0, all
729 sums are unchanged; the mono sums remain 1, so each color retains a
pure mono PM in C'.  Conversely extend by zero weights.
Hence an INFEASIBLE verdict for the all-nonzero problem on C alone is not a
certificate of weight-infeasibility of C; sub-colorings must be considered.
(This matters below: e.g. the P1-buggy model of the earlier session had
linear solution (1-t2, t2, t1, t1, 1, 1) and the unique lift relation
t1(1-2t2)-... = t1 = 0, forcing x2 = x3 = 0; that model also violated P1 and
is void; a correct zero-coordinate analysis of the analogous clean
configurations is still open.)

## 5. Computations run 2026-09-03 (all mono class (0,4,8); K slots per pair)

Legend: UNSAT = no structural configuration satisfies (b) no-new-mono and
(c) L3 together with P1 and the mono class; SAT = a configuration exists.
All SAT models are re-checked against the CNF and by brute_pass (P1 +
(b) + (c) with mono codes exactly {000,111,222}).

1. free-pairs-only K=2 (6 free pairs variable, forced pairs carry only
   their forced (i,i) slot):  UNSAT.  [COMPUTATIONAL; 0.2 s with Cadical153
   on the corrected encoder; result is monotone-robust: it was also UNSAT
   under the old weaker encoder, and UNSAT transfers to the corrected
   encoder.]  Consistent with the earlier z3 UNSAT (68 s, parallel_edges.md).

2. all-pairs K=2 (extra slots also allowed on the 9 forced pairs):  the
   earlier SAT claim (0.06 s) came from the buggy encoder (its model
   carried a duplicate (0,0) slot on (0,1)) and is VOID.  Corrected-encoder
   status: UNSAT [COMPUTATIONAL], independently confirmed by four solver
   engines (identical CNF; run_struct_engine.py each):
     - Cadical195: UNSAT in 887.9 s;
     - MapleCM:    UNSAT in 866.4 s;
     - Glucose4:   UNSAT in 2560.6 s;
     - Cadical153: UNSAT in ~56 min (the driver script crashed in
       model_to_slot_coloring(None) immediately after solve() returned
       model=None; that crash IS the UNSAT verdict — a SAT return would
       have carried a model).  All four verdicts are thus
       independently-confirmed UNSAT.
   Diagnostics supporting the verdict:  the same CNF with the L3 clause
   family disabled (build(no_l3=True)) is SAT (0.0 s, base graph H as
   model), so the CNF is not globally over-constrained and the UNSAT is
   attributable to the L3 family; the L3 encoding was additionally checked
   by inspection (per non-mono instance t:  [-g_t] v (v_j h_{tj}) where
   h_{tj} = g_t & g_j & (six per-vertex color equalities); pure-mono-pair
   h's are skipped).  Guided-DFS search (struct_dfs.py) and 30,000-config
   random sampling (0 clean of 27,176 (b)-ok ones) show clean
   (c)-configurations are very rare; simulated annealing over the K=2 space
   was also run (struct_anneal.py; see below).  Restricted-layer results
   with the corrected encoder [COMPUTATIONAL, Cadical153]:
     - extras allowed only on the 9 forced pairs, free pairs empty: UNSAT
       (0.3 s);
     - free pairs capped at 1 slot + extras on forced pairs: UNSAT (4.5 s);
     - free-pairs-only K=2, forced pairs bare: UNSAT (0.2 s).
   Hence every K=2 variant probed is UNSAT; in particular any K=2 clean
   configuration (if one existed) would have to use a free pair with two
   parallel slots, and even allowing extras on forced pairs does not help.
   Note (class-internal soundness of the search):  within the |P_i|=1 mono
   class (0,4,8) the presence of all nine forced (i,i) slots is forced:
   the only all-(i,i) PM of color i is the forced shape-m_i instance
   (extras on shape-m_i pairs cannot carry (i,i) by P1, and no other pair
   carries (i,i)), so a zero weight on any forced slot would make the
   color-i mono sum 0 != 1.

   Cascade documentation (the reason clean configurations are rare): the
   minimal code-450 partner on forced-pair extras is the shape-4 twin
   {(0,2):(0,2),(1,4):(0,2),(3,5):(1,1)}.  Config C2 = H + those two
   extras realizes code 450 twice (shape 1 and the shape-4 twin) but its
   partial variants (0,2)-extra/(1,4)-forced and (0,2)-forced/(1,4)-extra
   realize two new singleton codes 372 and 442.  No single extra slot on
   any pair fixes 372 or 442 [COMPUTATIONAL, enumerated]; partner instances
   require coordinated multi-slot additions, and naive partner candidates
   collide with (b): e.g. (1,3):(1,1) plus (4,5):(1,1) would make the new
   pure-mono-1 PM {13,02,45}.

3. all-pairs K=3:  earlier SAT claim VOID for the same reason.  Corrected
   run (Cadical153, StructSolver(3, *(0,4,8), extra_on_forced=True),
   same CNF build + solve pipeline as the K=2 runs):  NO VERDICT.  The
   process was killed by the background-task lifetime cap after exactly
   60 min with no output (all learned-clause progress in-memory and lost;
   started 14:08, killed 15:08).  Neither UNSAT nor SAT is claimed;
   the K=3 layer of the (0,4,8) class is OPEN.  Context: the K=2 instance
   needed 14.5-56 min across engines, so a K=3 resolution plausibly needs
   materially more than 60 min; K=3 also has far more instances (three
   slots per pair).  [COMPUTATIONAL: attempted; UNRESOLVED]

4. Weight layer:  the only fully-decided instance so far (the VOID P1-buggy
   model) resolved as weight-INFEASIBLE-by-zero-coordinate-contradiction
   [PROVED by hand, recorded here as a method demonstration]: mono rows
   force x4=x5=1, the lift relation forces x2=x3=0, hence slots (0,1)-a and
   (0,1)-b both have weight 0, but the color-0 mono row then sums to 0 != 1.
   With the P1-corrected encoder this exact configuration no longer occurs.

## 5b. Search-quality evidence (informational, no decision value)

- 30,000 random P1-clean K=2 configs near the base graph: 27,176 satisfy
  (b) + mono coverage, 0 of them satisfy (c) [COMPUTATIONAL].
- Guided DFS (struct_dfs.py): trivially exhausted at the first level (a
  single extra slot never directly duplicates a realized code, so the
  single-step "helps" gate blocks all moves — documented as a design
  lesson for cascading constraints).
- Simulated annealing over the full K=2 space (struct_anneal.py, ~1100
  restarts x 4000 steps total): no cost-0 configuration found; near-misses
  at cost 1 are mostly the base graph itself (annealing could not push
  through the cost valleys of the cascade).
- Deterministic cascade probes from the hand-built C2 (base + two code-450
  partner extras): the resulting singleton codes 372 and 442 admit NO fix
  by one additional slot (enumerated: every candidate adds >= 1 new
  singleton) and NO fix by two additional slots (5,583 pairs enumerated)
  [COMPUTATIONAL].  Partner instances for the singletons require >= 3
  coordinated new slots each, and each new partner spawns further
  singletons — the cascade appears to grow in required depth at every
  level for every extension tried (informational).

## 6. Mathematical proof attempts (Q1 elimination route)

Attempted route (mirroring parallel_edges.md's "mixed color pair single-edge
replacement"):  starting from a supposed multigraph witness, use the
S(v,k)=1 vertex constraints to force a single-edge replacement that kills
the parallel pair and preserves all 729 sums.  Status: no proof obtained.
The obstruction:  S(v,k) constraints are linear consequences of the mono/
group rows only when P_i has a single member for the color of v's edge; the
analysis always returns to the instance-level linear system A x = b plus
lift relations, whose C-points the numeric machinery above probes.  The
S(v,k)-argument skeleton and its failure mode are recorded in
proof/parallel_edges.md (unchanged); nothing in this session advanced the
purely combinatorial side beyond the structure notes of section 2.

## 7. Status summary (honest labels)

- Q1: OPEN.  No (6,3) multigraph witness is known; the restricted
  mono-class-(0,4,8) layer is closed up to two slots per pair by
  four-engine-consistent UNSAT (below) and remains open at >= 3 slots per
  pair (K=3: no verdict within the 60-min run budget).  No disproof of the
  elimination claim.
- Structural layer under mono class (0,4,8), P1-clean, exactly-one-mono-PM
  per color:  free-pairs-only K=2 UNSAT [COMPUTATIONAL]; all-pairs K=2
  UNSAT [COMPUTATIONAL, four independent engines: Cadical153, Cadical195,
  MapleCM, Glucose4 — section 5]; all-pairs K=3: UNRESOLVED (60-min
  timebox, no verdict — section 5 item 3).  The 24 other mono-shape
  classes and |P_i| > 1 mono classes are untouched.
- Weight layer: machinery complete (exact + 60-digit full-sum verification);
  exercised on the VOID model only.  Zero-coordinate sub-coloring subtlety
  (Lemma W1) documented; INFEASIBLE certificates must address it.
- Encoding bug found and fixed in the structural SAT; earlier SAT-model
  claims voided; UNSAT claims survive by monotonicity; self-tests pass.

## 8. Sharpest next moves

1. all-pairs K=2 is now CLOSED (UNSAT, 4 engines, mono class (0,4,8)).
   The next structural layer is all-pairs K=3, which got no verdict in 60
   min (background-task lifetime cap killed it; in-memory progress was
   lost).  Re-run K=3 in a way that survives beyond 60 min (detached
   process writing a proof-oblivious checkpoint, or run on the K=2-style
   per-engine drivers and let it exceed an hour), and/or pre-shrink the
   CNF (the K=3 instance count is the bottleneck; symmetry-breaking on
   free pairs and on the three mono colors would cut it substantially).
2. Weight decisions on P1-clean structural models (none known for this
   class yet): FEASIBLE (full 729-sum verification at 60 digits) would be
   a multigraph (6,3) witness — a counterexample to Q1 as stated here —
   worth immediate scrutiny against the |P_i|=1 restriction; INFEASIBLE
   certificates must respect Lemma W1.
3. Proof route that the K=2 result now makes plausible:  every clean
   configuration must use a pair with >= 3 parallel slots (from K=2 UNSAT
   under (0,4,8)); argue that any (b)+(c)-clean config with a k-slot pair
   spawns one with a (k+1)-slot pair ("cascade never terminates") — the
   C2 probes in section 5b are the pattern to formalize (every fix of
   codes 372/442 needed >= 3 coordinated new slots and each new partner
   spawned new singletons).  Such a structural no-configuration proof
   would NOT need the weight layer at all.
4. For a genuine Q1 proof, the |P_i|>1 mono classes and all 24 mono-shape
   classes need the same treatment (only (0,4,8) has been probed), or a
   global argument replacing the per-class analysis.
