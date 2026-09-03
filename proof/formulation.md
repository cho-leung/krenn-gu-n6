# (6,3) Formulation and Reductions — KG-P1

Snapshot 2026-08-28. Labels: PROVED / COMPUTATIONAL / CONJECTURAL.

## Problem (frozen)

Bi-colored weighted graph on 6 vertices (simple K_6 subgraph, possibly
multigraph): each edge e={u,v}, u<v, carries an ordered color pair
(c1,c2) ∈ {0,1,2}^2 (c1 at u, c2 at v; monochrome iff c1=c2) and a complex
weight w_e.  For a perfect matching M: IVC(M) = vertex coloring where each
vertex takes the color of its incident M-edge at that vertex.  For a
vertex coloring σ: w(σ) = Σ_{M: IVC(M)=σ} Π_{e∈M} w_e.
(6,3)-solution: w(000)=w(111)=w(222)=1 and w(σ)=0 for all other σ ∈ {0,1,2}^6.

## Reductions (all used by computation/search_core.py)

R1 [PROVED] All-nonzero WLOG: edges with w_e=0 contribute nothing; delete them.
R2 [PROVED] Simple case reduces to K_6: μ monotone under adding edges
   (zero-weight extension); any simple witness lifts to a K_6 witness.
R3 [PROVED] IVC(M) is monochrome of color i iff every edge of M is (i,i).
   Hence the three monochrome PM sets are P_i = PM(H_i) where H_i is the
   subgraph of (i,i)-edges; H_0, H_1, H_2 pairwise edge-disjoint, each with ≥1 PM.
R4 [PROVED] The 729 equations decompose per realized IVC: for each i:
   Σ_{M∈P_i} x_M = 1; for each realized non-mono σ: Σ_{M:IVC(M)=σ} x_M = 0.
   Unrealized IVCs contribute 0 automatically.  (x_M := Π_{e∈M} w_e.)
R5 [COMPUTATIONAL] Liftability: the map f: (C*)^15 → (C*)^15, w ↦ (x_M)_M
   has image exactly {x : Π_M x_M^{c_M} = 1 for all c ∈ ker U^T}, where U is
   the 15×15 PM–edge incidence matrix of K_6.  Computed: rank(U) = 10,
   ker U^T has dimension 5 (relations from pairs of distinct 1-factorizations
   of K_6).  [For subgraphs, ker is computed per subgraph.]
R6 [PROVED] Generic threshold: the affine solution space L of the linear
   system (dim k = 15 − rank(A)) intersects the image generically iff
   k ≥ rank(U') (=10 for full K_6); cases k < 5 are solved exactly
   (k=0: rational check; k=1: gcd; k≥2: numeric+nsimplify / groebner).

## Decision procedure (search_core.decide)

Coloring → surviving PMs S (absent edges kill PMs) → mono sets P_i and
non-mono IVC groups → linear system A x = b (3+g rows) over Q → solution
space L → intersect with image relations, all coordinates nonzero.
FEASIBLE ⇒ exact witness x (rational or algebraic); INFEASIBLE ⇒ certified
reason; UNRESOLVED ⇒ rare unsolved relation system.

## Validation

[COMPUTATIONAL, exhaustive 3^15 scan, 2026-08-28] Monochrome-edge-only
colorings of K_6: 248,310 realize all three mono IVCs; **0 pass the
two-or-more-PMs-per-group condition (L3)**.  Hence mono-edge (6,3) is UNSAT.
This independently reproduces Cervera-Lierta–Krenn–Aspuru-Guzik
(Quantum 6:836, 2022) for n=6 with a stronger, trivially checkable
certificate: mono-realized ⇒ some non-mono IVC has exactly one PM.

## Open lemmas (proof-side targets)

L-A [CONJECTURAL, suggested by exhaustive data] Any monochrome-edge coloring
   of K_6 realizing all three monochrome IVCs has a singleton mixed-IVC
   group.  (If proved: mono-edge UNSAT in two lines.)
L-B [CONJECTURAL] In any (6,3)-solution with all-nonzero weights, every
   realized non-mono IVC has ≥ 2 PMs (L3) — PROVED: otherwise x_M = 0 forces
   a zero weight.  [This is R7, proved.]
L-C [OPEN] Parallel-edge elimination: multigraph (6,3) witness ⇒ simple
   witness?  Same-pair parallel edges merge (w→w1+w2) [PROVED]; distinct-pair
   parallel edges open.
