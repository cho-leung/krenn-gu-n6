# The Krenn–Gu conjecture holds for all simple graphs on six vertices

**Theorem.** For every number of colors D ≥ 3, there is no bi-colored
weighted *simple* graph on 6 vertices — bichromatic edges and complex
weights allowed — in which all D monochromatic inherited vertex colorings
have unit weight while every other vertex coloring has weight zero.
Equivalently, the matching index satisfies μ(G) ≤ 2 for every simple graph
G on 6 vertices (over any integral domain: ℂ, ℝ, ℤ, trinary {−1,0,1}).

This settles the DeepMind *formal-conjectures* open statements
`eqSystem6_no_solution_d3`, `_d4`, `_d5`, `_ge3` and their `_real`,
`_int`, `_trinary_int` variants where present — **13 open statements**.

The full Krenn–Gu conjecture (arbitrary even n ≥ 8, and multigraphs with
parallel edges at n = 6) remains open; the €3,000 bounty
([Mario Krenn's prize page](https://mariokrenn.wordpress.com/graph-theory-question/))
is **not** claimed by this work.

## How the proof works

The argument is weight-free: a solution forces D pairwise edge-disjoint
nonempty monochromatic perfect-matching classes (each ≥ 3 edges, so
3D ≤ 15, i.e. D ≤ 5), and every surviving coloring must satisfy two
purely combinatorial conditions:
- **(b)** no perfect matching outside its class realizes a monochrome
  inherited vertex coloring, and
- **(c)** (L3) every realized non-monochromatic coloring is realized by
  at least two perfect matchings.

Exhaustive enumeration eliminates every candidate:

| D | raw classes | S₆ orbits | assignments | survivors |
|---|---|---|---|---|
| 3 | 5,610 | 24 | 2,033,610 | **0** |
| 4 | 2,160 | 5 | 4,917 | **0** |
| 5 | 720 = 6·5! | 1 | 1 | **0** |
| ≥ 6 | — | — | — | trivial (3D ≤ 15) |

## Repository contents

- `paper/` — the paper (LaTeX source + PDF): "The Krenn–Gu conjecture
  holds for all simple graphs on six vertices".
- `proof/` — the reduction lemmas, the certificates
  (`certificate_simple63.md`, `certificate_d45.md`), the multigraph
  analysis (`parallel_edges.md`, `parallel_edges_Q1_attack_2026-09-03.md`),
  and the n=8 attack draft.
- `computation/` — the exhaustive search pipeline (Python 3.9 + numpy +
  sympy): `gen_search.py` (class enumeration + batch), `search_core.py`
  (exact decision procedure), and the mono/t111 scans.
- `audit/` — independent verification: `AUDIT_REPORT_2026-09-03.md`,
  `AUDIT_REPORT_D45_2026-09-03.md`, and `verification_2026-09-03/`
  (fresh re-implementations, naive-filter replays, z3 independent
  confirmations, positive controls).
- `lean/` — Lean 4 formalization of the certificates (stdlib-only,
  `native_decide`): see `lean/PLAN.md` and `lean/kg6/`.
- `research_os/` — the project's state/claim/artifact ledgers.

## Reproducing the verification

```bash
cd computation
python3 -c "from k6_basics import *; print('15 PMs, rank(U)=', incidence_matrix().rank())"
python3 gen_search.py          # ~seconds: 24 orbits, 2,033,610 rows, 0 survivors
cd ../audit/verification_2026-09-03
python3 indep_basics.py        # independent re-derivation of the basics
python3 indep_triples.py       # 5,610 raw triples, orbit completeness
python3 indep_filter_batch.py  # batch replay with a fresh filter
python3 indep_d45_check.py     # D=4/D=5 cross-checks (raw counts, orbits, z3)
```

Lean (requires the Lean 4 toolchain):

```bash
cd lean/kg6 && lake build      # the certificates as kernel-checked theorems
```

## Status

- **DONE**: n = 6, simple graphs, all D ≥ 3 (exhaustively certified,
  independently audited 2026-09-03).
- **IN PROGRESS**: multigraph n = 6 (parallel edges). Structural evidence:
  four independent SAT engines (Cadical195 888 s, MapleCM 866 s,
  Glucose4 2561 s, Cadical153 ~56 min) prove the K=2 structural layer
  UNSAT under the corrected encoder
  (`proof/parallel_edges_Q1_attack_2026-09-03.md`); K=3 remains open.
- **OPEN**: n ≥ 8.

## Author

Junhao Liang (梁竣皓) — independent researcher.
JunhaoLiang2005@gmail.com

*This research was conducted with substantial assistance from AI systems
(Anthropic's Claude). Every mathematical claim was independently
re-verified by fresh implementations and by independent symbolic solvers;
no result is asserted without the verification recorded under `audit/`.*
