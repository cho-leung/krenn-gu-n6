# (6,D) for D=4,5 — exhaustive certificate (2026-09-03)

Companion to proof/certificate_simple63.md (D=3). Same problem, D colors,
simple graphs, integral-domain weights.

## Claim
For D=4 and D=5, no bi-colored weighted simple graph on 6 vertices
(D colors, bichromatic edges, complex weights) realizes all D
monochromatic IVCs with unit weight and all others 0.

## Certificate chain

1. Reductions: identical to the D=3 case (R1 all-nonzero WLOG; R2 K_6
   suffices; R3 mono PM structure; R4 per-IVC decomposition; R7/L3) —
   all field-independent (proof/simple_case_reduction.md).
2. Elementary bound (Lemma, proof in paper/main.tex): a (6,D)-solution
   forces D pairwise edge-disjoint nonempty mono PM classes, each with
   >= 3 edges, so 3D <= 15, i.e. D <= 5. Hence D=3,4,5 exhaust all
   possible color counts.
3. Exhaustive enumeration (audit/verification_2026-09-03/compute_d45.py):
   - D=4: 2,160 ordered quadruples of nonempty pairwise edge-disjoint PM
     subsets -> 5 S_6 orbit reps (listed in paper Appendix A); free edges
     F <= 3 (17 options each); complete batch 4,917 rows; EVERY row fails
     no-new-mono or L3. 0 survivors.
   - D=5: 720 = 6*5! ordered quintuples (each = an ordered
     1-factorization of K_6; multi-PM classes are impossible since
     5 + 12 > 15) -> 1 orbit; F = 0; the single assignment fails the
     conditions.
4. Independent cross-checks
   (audit/verification_2026-09-03/indep_d45_check.py):
   - D=4 raw count re-derived by the independent formula
     sum over the 5,610 audited triples of (2^{c(T)} - 1): 2,160.
   - D=5 raw count by 6 * 5! = 720.
   - Orbit completeness: every raw class's canonical key re-computed and
     matched to the stored reps (5/5 and 1/1, no missing, no redundant).
   - Full batch replayed with an independent naive tuple-based filter:
     4,917 and 1 rows, 0 survivors, no filter disagreement.
   - z3 independent encoding of (b)+(c): UNSAT 5/5 (D=4) and 1/1 (D=5).

## Consequences
Together with D=3 (certificate_simple63.md) and the elementary D<=5
bound: the Krenn-Gu conjecture holds for ALL simple graphs on 6
vertices and all D >= 3. Settles the DeepMind formal-conjectures
statements eqSystem6_no_solution_d3 (C/R/Z/trinary), _d4 (C), _d5
(C/R/Z/trinary), _ge3 (C/R/Z/trinary) — 13 open statements in total.
(d6 was already recorded solved; it also follows from the D<=5 bound.)

## Remaining gap
Multigraphs (parallel edges) at n=6 (Q1, proof/parallel_edges.md and
proof/parallel_edges_Q1_attack_2026-09-03.md), and all n >= 8.
