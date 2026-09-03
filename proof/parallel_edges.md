# Parallel-edge analysis (multigraph (6,3)) — KG-P1 worknotes

Snapshot 2026-08-28. Labels per protocol.

## Setting

Multigraph on 6 vertices: per vertex pair {u,v}, a multiset of edges, each
with a distinct color pair (same-pair parallels merge: w -> w1+w2 [PROVED],
and a merged zero deletes the edge).  All weights nonzero WLOG [R1].

## Key decomposition

For a vertex pair {u,v} with parallel edges e_j = (p_j, w_j), p_j distinct:
the PMs through e_j are {e_j + N : N in PM(G - {u,v})}, with IVC
  sigma_j(N) = sigma(N) with u -> p_j(1), v -> p_j(2).
Each such family contributes to the group sums with x = w_j * w(N).

## Lemma P1 [PROVED]
Same-pair parallel edges merge: replacing e1,e2 (same pair p, weights w1,w2)
by one edge (p, w1+w2) preserves every IVC-group sum exactly (and zero
deletes).  Hence WLOG per vertex pair the color pairs are distinct.

## Lemma P2 [PROVED]
Self-cancelling families delete: if for some parallel edge e_j = (p_j, w_j)
the family sums  s_j(sigma) := sum_{N : sigma_j(N) = sigma} w(N)  vanish for
every sigma, then deleting e_j leaves all group sums unchanged (each group
loses exactly w_j * s_j(sigma) = 0).

## Question Q1 [OPEN] (parallel-pair elimination)
Can a multigraph (6,3)-witness exist with two distinct-pair parallel edges
between some vertex pair?  Equivalently: is every multigraph witness
reducible (via P1/P2-style moves) to a simple witness?
If Q1 = NO: multigraph (6,3) reduces to the simple case.

## Evidence
- (1,1,1)-class exhaustive scan: no simple assignment passes L3 even with
  absent edges (so simple witnesses need >= 2 PMs in some mono class if
  they exist at all).
- Distinct-pair parallels double PM families with fixed IVC-offset
  (u,v get different colors) — new groups arise; whether they can all be
  satisfied simultaneously is exactly the multigraph search question.

## Planned attack
1. If simple case resolves UNSAT: run a bounded multigraph search
   (distinct-pair sets per vertex pair, capped multiplicity) via the same
   class + z3 machinery, extended to multi-slots.
2. Try to prove Q1 by the family-sum argument: for any witness with a
   distinct-pair parallel edge, show either P2 applies (deletable) or the
   non-cancelling family forces a contradiction with the mono sums.

## Vertex-constraint machinery [PROVED]
For ANY (multigraph) solution and every vertex v, color k:
   S(v,k) := sum_{M: v maps to k in IVC(M)} x_M = 1
(only the monochrome coloring kkk contributes among IVC sums).
With parallel edges e_j = (p_j, w_j) = ((a_j,b_j), w_j) at {u,v} and
T := sum_{N in PM(G - {u,v})} w(N), this gives
   S(u, a_j) = w_j T + R_j = 1,
where R_j sums the x_M over PMs matching u through OTHER edges (disjoint
PM sets for distinct a_j).  Hence
   w_2 (1 - R_1) = w_1 (1 - R_2),   T = (1-R_j)/w_j.
Case tree: G - {u,v} has 0..3 PMs on 4 vertices; R_j decomposes over
u's other neighbors.  Bounded hand-checkable case analysis — next step
for a proof of Q1 (distinct-pair parallel elimination).

## Probe results
- K=2 (distinct-pair slots on free pairs only): UNSAT [68s].
- K=2 WITHOUT distinctness: SAT but only via same-pair duplicates
  (P1-mergeable; merged coloring is INFEASIBLE with 5 singleton groups) —
  confirms P1 and the necessity of the distinctness constraint.
- K=3: z3 timeout at 300s (encoding too large); rerun pending.

