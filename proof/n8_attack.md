# n=8 attack sketch (KG-P2 direction) — drafted during KG-P1

## Known state for (8,3)
- Cervera-Lierta et al. (Quantum 6:836): SAT-UNSAT only for (8, d >= 4),
  monochrome edges.  (8,3) is OPEN even for monochrome edges.
- DeepMind formal-conjectures: eqSystem8_no_solution_d3 open over C/R/Z/trinary.
- CGI (MFCS 2024): no direct (8,3) statement; minimal counterexample must be
  4-connected (any n).

## Machinery to port (from the (6,3) pipeline)
- R1 (all-nonzero), R2 (K_n suffices for the simple case), R3 (P_i = PM(H_i)),
  R4 (per-IVC decomposition), R5 (lift relations via ker U^T; for K_8:
  U is 105 x 28, rank <= 28, ker U^T has dim >= 77), R7 (L3).
- Generic feasibility threshold: solution space dim k must satisfy
  k + rank(U') >= |S| for a generic intersection with the image.

## Differences from n=6
1. PM count 105; class enumeration over 4^105 raw is infeasible — needs
   canonical (orderly) enumeration of disjoint (P0,P1,P2) plus symmetry.
2. Free-edge count F = 28 - |forced| can be large (up to ~22); batch
   enumeration impossible -> z3/SAT with model iteration, or smarter
   invariants to prune.
3. The mono-edge (8,3) case is itself open — first target: settle mono-edge
   (8,3) (L3-style analysis + rank/relations).  A mono-edge (8,3) witness
   would already refute the conjecture.
4. Relations: 77+ monomial relations — the image is 28-dimensional at most;
   the linear-system rank per coloring is small (rows have disjoint supports,
   rank = 3 + g); with |S| = 105: k = 102 - g: generic feasibility requires
   k >= 28, i.e., g <= 74: the mixed PMs must realize <= 74 distinct IVCs
   (out of 3^8 = 6561 possible) — a strong clustering constraint.

## Priorities
1. Mono-edge (8,3): does L3 ever pass? (vectorized scan feasible over
   constrained classes.)
2. If mono-edge (8,3) is UNSAT: the full (8,3) needs bichromatic/multigraph
   analysis — port the (6,3) class search with z3 iteration.
3. Any (8,3) witness = counterexample to the conjecture (d=3 >= 3, n=8 > 4).
