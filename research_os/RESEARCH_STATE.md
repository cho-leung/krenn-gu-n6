# RESEARCH STATE — Krenn–Gu Conjecture (KG-P1, major result recorded)

Snapshot: 2026-08-29. Phase: KG-P1 ACTIVE — simple case RESOLVED (UNSAT);
multigraph case in progress.

## ★ SIMPLE (6,3) UNSAT — exhaustive computational theorem

**Claim [COMPUTATIONAL, exhaustive]:** No bi-colored weighted SIMPLE graph on
6 vertices (bichromatic edges, complex weights) realizes dimension 3.

**Certificate chain:**
1. Reductions (proof/simple_case_reduction.md): R1 all-nonzero WLOG; R2 K_6
   suffices; R3 P_i = PM(H_i) with pairwise edge-disjoint H_i; R4 per-IVC
   decomposition; R7 (L3) every realized non-mono IVC needs >= 2 PMs.
2. Complete class enumeration (computation/gen_search.py, direct
   construction): 5,610 valid triples (P0,P1,P2) -> 24 canonical orbits
   under S_6.  Class sizes are edge-budget-forced: only (1,1,1)...(4,1,1),
   (1,1,2),(1,1,3),(1,1,4),(1,2,1),(1,2,2),(1,3,1),(1,4,1),(2,1,1),
   (2,1,2),(2,2,1),(2,2,2),(3,1,1),(4,1,1) occur.
3. Exhaustive batch: all 2,033,610 free-edge assignments (options: 9 color
   pairs + absent; F <= 6 for every class): EVERY one fails L3 or
   no-new-mono.  Zero survivors reached the linear/relation stage.
   [2026-09-03: 2,033,610 is the independently re-derived count; the
   earlier figure 2,032,554 was a transcription error.]
4. Independent confirmation: z3 UNSAT on all 24 classes
   (audit/verification_2026-09-03/indep_z3_spotcheck.py, 24/24 UNSAT);
   t111 numpy scan 0/1,000,000 per (1,1,1) rep; mono-edge subcase
   reproduces Cervera-Lierta et al. (Quantum 6:836) for n=6.

**Consequences:**
- Settles the DeepMind formal-conjectures open statements
  eqSystem6_no_solution_d3 (C), _d3_real (R), _d3_int (Z),
  _d3_trinary_int ({-1,0,1}) — simple case. NOT settled: d4 (4 colors),
  d5 (5 colors), ge3 (all D >= 3) — separate enumerations needed
  [corrected 2026-09-03].
- The obstruction is PURELY COMBINATORIAL (L3), no weight/relation
  machinery needed at n=6.

**Not yet covered:** multigraphs (parallel edges) at n=6; all n >= 8.

## ★★ (6,D) for D=4,5 — UNSAT (2026-09-03): all simple n=6 resolved

Same method, generalized to D colors [COMPUTATIONAL, exhaustive; audited
2026-09-03, report audit/AUDIT_REPORT_D45_2026-09-03.md, certificate
proof/certificate_d45.md]:
- D=4: 2,160 classes -> 5 S_6 orbits -> 4,917 assignments -> 0 survivors.
- D=5: 720 = 6*5! classes (ordered 1-factorizations) -> 1 orbit -> 1
  assignment -> fails (b)/(c).
- Elementary: a (6,D)-solution needs D disjoint nonempty mono classes of
  >= 3 edges each, so 3D <= 15, D <= 5. Together with D=3: **the
  Krenn-Gu conjecture holds for ALL simple graphs on 6 vertices, all
  D >= 3** (any integral domain).
- Settles the DeepMind formal-conjectures statements
  eqSystem6_no_solution_d3/_d3_real/_d3_int/_d3_trinary_int, _d4,
  _d5/_d5_real/_d5_int/_d5_trinary_int, _ge3/_ge3_real/_ge3_int/
  _ge3_trinary_int (13 open statements; d6 was already recorded solved).
- Paper upgraded: paper/main.tex (8 pp), "The Krenn--Gu conjecture holds
  for all simple graphs on six vertices".

## Multigraph (6,3) status
- P1 [PROVED] same-pair parallels merge; P2 [PROVED] self-cancelling
  families delete (proof/parallel_edges.md).
- Probes: K=2 distinct slots on free pairs: UNSAT (68s z3). K=2 all pairs:
  UNKNOWN (1h). K=3: UNKNOWN (45min).  z3 encodings saturate — needs Q1
  (parallel elimination proof) or bit-blasted SAT.
- Vertex-constraint machinery derived (S(v,k)=1 identities) for the Q1
  case analysis (proof/parallel_edges.md).

## Files
- computation/: k6_basics, search_core (exact decision procedure),
  run_search (mono + t111), gen_search (all classes, cached enumeration),
  verify_witness, package_witness, analyze_survivors, multi_probe(2).
- proof/: formulation.md, simple_case_reduction.md, parallel_edges.md,
  certificate_simple63.md, n8_attack.md.
- Artifacts: computation/triples_cache.pkl (24 canonical classes),
  survivors.jsonl (empty: 0 survivors), mono/t111 logs.

## Next (current focus)
1. Q1: prove distinct-pair parallel edges are eliminable => multigraph
   (6,3) UNSAT follows from the simple-case result.
2. If Q1 resists: bounded multigraph search via bit-blasted SAT (pysat).
3. n=8 attack (proof/n8_attack.md) — KG-P2 proposal.

## INDEPENDENT AUDIT (2026-09-03)
Full independent verification of the simple (6,3) claim, from scratch
(audit/verification_2026-09-03/, report audit/AUDIT_REPORT_2026-09-03.md):
5,610 raw triples and 24-orbit completeness re-derived; batch re-run with
a fresh filter (2,033,610 rows, 0 survivors); mono scan re-derived
(248,310 pass (a), 0 pass (a)+L3 — the mono_validation.log count 211,590
came from a superseded filter version and does not affect any verdict);
z3 UNSAT 24/24; independent exact engine agrees with search_core.decide on
500+ cross-check instances and passes positive controls. Verdict: PASS.
Certificate filled: proof/certificate_simple63.md.
