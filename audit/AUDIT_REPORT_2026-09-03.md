# INDEPENDENT VERIFICATION AUDIT — Simple (6,3) UNSAT

- Date: 2026-09-03
- Auditor: independent session (Claude Code), fresh implementations
- Scope: the claim "No bi-colored weighted SIMPLE graph on 6 vertices
  (bichromatic edges, complex weights) realizes dimension 3"
  (research_os/RESEARCH_STATE.md, KG-P1), as produced by
  computation/gen_search.py + run_search.py + search_core.py on 2026-08-28/29.
- Method: all core logic re-implemented from scratch in
  audit/verification_2026-09-03/ (no import of computation/*.py decision
  logic; only shared edge/PM index data). z3 used as an independent
  symbolic backend.
- **VERDICT: PASS** (with notes N1–N7; none affect the verdict)

## 1. Verification chain (all independent)

| # | Item | Result |
|---|---|---|
| V1 | K_6 basics: 15 PMs, rank(U)=10 over Q and F_2, dim ker U^T = 5, pair-of-1-factorization relations span ker U^T | CONFIRMED (indep_basics.py) |
| V2 | Raw triple enumeration: 5,610 ordered (P0,P1,P2) of nonempty pairwise edge-disjoint PM subsets | CONFIRMED (indep_triples.py) |
| V3 | Orbit reduction: the 24 cached reps are complete and non-redundant (every raw triple's canonical form is among the 24; pairwise inequivalent; all valid) | CONFIRMED (indep_triples.py) |
| V4 | Batch re-run with a fresh filter (naive reference cross-checked vs vectorized on 20,000 random rows): 2,033,610 rows, 0 survivors of no-new-mono + L3 | CONFIRMED (indep_filter_batch.py) |
| V5 | Their current filter code (run_search.l3_and_g_filter / l3_group_filter) agrees with the independent naive reference on 60,000 random rows (including mono-only colorings) | CONFIRMED (indep_cross_their_filter.py) |
| V6 | z3 UNSAT for the no-new-mono + L3 constraints on all 24 classes | CONFIRMED 24/24 (indep_z3_spotcheck.py) |
| V7 | Mono-edge subcase re-derived: 248,310 of 14,348,907 mono colorings realize all three mono IVCs; **0 pass L3** | CONFIRMED (indep_mono_scan.py) |
| V8 | Independent exact engine (indep_engine.py, fresh implementation): agrees with search_core.decide on 300 random colorings and 200 mono (a)-passers (100% agreement); positive controls pass — (4,3) K_4 known dimension-3 example returns FEASIBLE with exact 3^4-sum verification; relaxed instances exercise the lift-relation machinery (k=0 and k=1 paths) | CONFIRMED (indep_engine_tests.py) |

The exhaustive theorem therefore rests on: proved reductions R1–R4/R7
(simple_case_reduction.md, re-read and sound), a complete class cover (V2+V3),
a complete per-class enumeration (V4), and a sound filter (V5) implementing
exactly the two combinatorial conditions (no-new-mono, L3). No decide() call
is needed anywhere: zero survivors. The only remaining soundness-critical
component, the filter, is validated three ways (naive reference, their-vec vs
naive, z3).

## 2. Discrepancies found and resolutions

- **D1 — batch count**: RESEARCH_STATE.md recorded "2,032,554" free-edge
  assignments; the actual total (re-derived twice) is **2,033,610**.
  Transcription error; fixed in RESEARCH_STATE.md.
- **D2 — mono scan count**: mono_validation.log records 211,590 survivors
  of the (a)+L3 filter, while formulation.md/simple_case_reduction.md
  record "248,310 pass (a); 0 pass (c)". The **documents are correct**
  (V7); the log's 211,590 came from a superseded filter version. The run's
  final verdict (feasible=0) is unaffected: decide() rejects every such row
  by its own exact L3 check (R7), before any linear algebra — this also
  explains the log's 12 s decide phase. No correction needed in the docs;
  the log is superseded (noted here for provenance).
- **D3 — stale status**: simple_case_reduction.md "Status" section said
  "RUNNING (gen_search.py, ~3290 canonical classes)" — stale; fixed to the
  final counts (24 classes, 2,033,610 rows) with audit pointers.
- **D4 — empty certificate**: proof/certificate_simple63.md was an unfilled
  template; filled with the final counts and the verification chain.
- **D5 — registry sync**: APPROACH_REGISTRY.yaml A-011 still said
  "PROPOSED (KG-P1, not authorized)"; updated (simple case RESOLVED via
  exhaustive enumeration; SMT/Gröbner route available for multigraph/n>=8).
- **D6 — unsupported confirmation claims**: RESEARCH_STATE.md cited "z3
  UNSAT on all spot-checked classes" and "brute-force Counter cross-check"
  with no artifacts. The z3 confirmation is now on file (V6, 24/24); the
  "Counter cross-check" has no trace in the code — V5's naive-reference
  cross-check (60,000 rows) now covers the filter at greater depth.

## 3. Code findings (non-blocking)

- **N1 (latent bug, never executed)**: search_core.decide k=1 gcd loop
  calls `sp.expand(gpoly)` on an object that is a Poly from the second
  iteration — raises AttributeError. In the actual runs this path is
  unreachable (zero survivors, and mono rows die at the L3 pre-check), so
  no result is affected. Recommend fixing for future relaxed-mode runs
  (same bug existed in the auditor's engine; fixed there).
- **N2 (silent-error pattern)**: run_search._decide_worker catches
  exceptions as ("ERROR", …) but run_mono's loop neither prints nor counts
  them separately — an ERROR-ing decide would be indistinguishable from
  INFEASIBLE. In the audited run this did not occur (V7 confirms all rows
  die at L3 before reaching fragile code; timing consistent). Recommend:
  treat ERROR as run failure in future scans.
- **N3 (untested FEASIBLE path of search_core.decide)**: no (6,3) input can
  reach the FEASIBLE branch (that is the theorem), so their decide's
  witness machinery has never executed. Mitigated by V8: an independent
  engine with verified FEASIBLE behavior (positive controls) agrees with
  decide on 500+ instances.
- **N4 (mono decide phase unnecessary)**: per V7 the historical decide pass
  over 211,590 rows was dead work caused by D2's buggy filter. Irrelevant
  to correctness.

## 4. Residual scope (not part of this audit)

- Multigraph (6,3): Q1 (distinct-pair parallel elimination,
  proof/parallel_edges.md) open; z3 probes UNKNOWN at K=2/K=3.
- n >= 8: open (proof/n8_attack.md).
- Governance note: CLAUDE.md still says "KG-P1 … NOT authorized — requires
  explicit GO from the user" while RESEARCH_STATE.md says KG-P1 ACTIVE.
  Resolution is a Root (user) decision; this audit performed verification
  only, and made no new mathematics claims.

## 5. Conclusion

The exhaustive computational theorem "simple (6,3) UNSAT" is verified. All
critical quantities (5,610 / 24 / 2,033,610 / 0 / 248,310 / 0) were
re-derived independently, the elimination conditions are the proved
combinatorial lemmas R3+R7, and an independent symbolic backend (z3)
confirms unsatisfiability on every class. The certificate
(proof/certificate_simple63.md) is now filled and machine-reproducible.
