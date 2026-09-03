# Simple (6,3): from the conjecture to a finite search

All statements here concern the SIMPLE case: bi-colored subgraphs of K_6
(no parallel edges), complex weights.  Labels: PROVED / COMPUTATIONAL.

## Definitions (frozen, KG-P0)
G = subgraph of K_6 on vertices 0..5; each edge e={u,v} (u<v) carries an
ordered color pair c(e)=(c1,c2) in {0,1,2}^2 (c1 at u, c2 at v) and weight
w(e) in C.  IVC(M) for a perfect matching M: vertex u gets the color of its
M-edge at u.  w(sigma) = sum over PMs M with IVC(M)=sigma of prod_{e in M} w(e).
(6,3)-solution: w(000)=w(111)=w(222)=1, all other w(sigma)=0.

## Lemma 1 (all-nonzero WLOG) [PROVED]
If a solution exists, one exists with all weights nonzero.
Proof: edges with w(e)=0 contribute 0 to every PM product; deleting them
removes only PMs whose product was 0, leaving every sum w(sigma) unchanged.
(The mono sums remain 1, so each color still has a surviving PM.)

## Lemma 2 (K_6 suffices) [PROVED]
If any simple graph on 6 vertices has a solution, K_6 does.
Proof: color the missing edges arbitrarily and give them weight 0; all new
PMs use a zero-weight edge and contribute nothing.

## Lemma 3 (mono PM structure) [PROVED]
IVC(M) = (i,...,i) iff every edge of M has c(e) = (i,i).
Proof: vertex u is colored i iff its M-edge has color i at u; all six
vertices colored i forces both endpoint colors of every M-edge to be i.

## Lemma 4 (per-IVC decomposition) [PROVED]
The 729 equations are equivalent to:
  (i)  sum_{M in P_i} x_M = 1  for i = 0,1,2,  where P_i = PMs whose IVC is
       monochrome of color i (x_M := prod_{e in M} w_e), and
  (ii) sum_{M: IVC(M)=sigma} x_M = 0  for every realized non-mono sigma.
Proof: sums over colorings decompose over the realized IVCs; unrealized
IVCs have empty sums.

## Lemma 5 (L3) [PROVED]
In a solution with all weights nonzero, every realized non-mono IVC has at
least two PMs.
Proof: a unique PM M realizing sigma would give w(sigma) = x_M != 0.

## Lemma 6 (liftability) [PROVED modulo the rank computation]
Let S be the PMs of the subgraph and U the |S| x |E| PM-edge incidence
matrix over Q.  A vector x in (C*)^|S| is of the form (prod_{e in M} w_e)_M
for some weights w in (C*)^|E| iff  prod_M x_M^{c_M} = 1 for every
c = (c_M) in ker U^T (rational exponents).
Proof sketch: taking componentwise logarithms, x -> u solves the linear
system U^T u = log x; solvable iff log x is orthogonal to ker U^T.
[COMPUTATIONAL] For G = K_6: rank(U) = 10 over Q and over F_2, and ker U^T
has dimension 5.  A basis of ker U^T is obtained from pairs of distinct
1-factorizations of K_6: for two 1-factorizations F, F' (both partition
E(K_6) into 5 disjoint PMs), the relation
        prod_{M in F} x_M = prod_{M in F'} x_M
holds, and these span ker U^T.
[For proper subgraphs, rank(U) and ker U^T are computed per case by the
verified script computation/k6_basics.py + search_core.py.]

## Theorem A (reduction to finite search)
A simple (6,3)-solution exists iff there exist a coloring of the 15 pairs
of K_6 (each edge: one of the 9 color pairs, or absent) such that:
  (a) each of P_0,P_1,P_2 (as in Lemma 3) is nonempty,
  (b) no PM outside P_0 u P_1 u P_2 has a monochrome IVC,
  (c) L3 holds (Lemma 5),
  (d) the linear system (Lemma 4) over Q has a solution space L of
      dimension k = |S| - rank(A), and
  (e) L intersects the image variety of Lemma 6 in a point with all
      coordinates nonzero.
The conditions (a)-(e) are decided exactly by computation/search_core.py.

## Status [COMPUTATIONAL, exhaustive — COMPLETE 2026-08-29, independently re-verified 2026-09-03]
- Monochrome-edge colorings: all 14,348,907; 248,310 pass (a); 0 pass (c).
- Single-PM classes (|P_0|=|P_1|=|P_2|=1): 2 canonical orbit classes;
  all 2,000,000 assignments fail (c).
- All classes: 5,610 raw triples -> 24 canonical orbit classes; complete
  batch enumeration of all 2,033,610 free-edge assignments; 0 pass (b)+(c);
  z3 UNSAT on all 24 classes (audit/verification_2026-09-03/).
- Independent verification: audit/verification_2026-09-03/ +
  audit/AUDIT_REPORT_2026-09-03.md; certificate: proof/certificate_simple63.md.
