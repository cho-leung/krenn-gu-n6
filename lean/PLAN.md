# Lean 4 Formalization Plan — (6,3) simple-case no-solution

Target: a Lean proof of the no-solution theorem (Theorem 2 / thm:main of the
paper), executable-computation certified, to be upstreamed into the DeepMind
formal-conjectures repository (statements eqSystem6_no_solution_d3 family).

## Toolchain

- Lean 4.33.1 via elan (manual download → `elan toolchain link` due to
  elan's download-timeout problem in this network; see session notes).
- mathlib via `lake` — REQUIRED for Fin, Finset, Sym/Equiv.Perm, Fin 3, etc.
  (mathlib download is also large; same manual-download fallback if needed.)

## Statement to prove (self-contained form)

Let V = Fin 6; E = all unordered pairs; a *coloring* assigns to each pair
either None (absent) or an ordered pair (a,b) : Fin 3 × Fin 3. A PM is a
3-edge cover; IVC : PM → Fin 3 → Fin 3... (precisely: color of each vertex
under its matching edge; only defined when all edges present).

Theorem (target):
  ¬ ∃ (coloring : Edge → Option (Fin3 × Fin3)) (w : Edge → R), R integral
  domain, (∀ e, w e ≠ 0 → coloring e ≠ None? ...)

SIMPLER equivalent over ℚ (paper's field-independence makes ℚ enough for the
repo's ℂ/ℝ/ℤ statements; trinary needs a separate transfer note):

  Define wSol (col) : Prop := ∃ w : {e // col e ≠ none} → ℚ, w nonzero,
    (∀ i, (Σ_{M ∈ PMS, IVC M = i^6} ∏_{e∈M} w e) = 1) ∧
    (∀ σ non-mono, (Σ_{M, IVC M = σ} ∏ w e) = 0)

  Theorem : ¬ ∃ col : Edge → Option (Fin3 × Fin3), wSol col.

## Proof architecture (mirrors the paper)

1. **Data**: `Edge` = Sym2 (Fin 6) (or the Finset of 15 pairs), `PM` = Fin 6
   ≃ Fin 6 without fixed points mod 2 (or a Finset of 15), 15 PMs as a
   Finset, `coloring` as function, IVC as function, mono codes i^6.

2. **Reduction lemmas** (pure mathlib combinatorics, no computation):
   - L1 all-nonzero WLOG: if wSol col then wSol' col with all-nonzero w.
   - L3 mono-PM structure: IVC M = i^6 ↔ all edges of M colored (i,i).
   - L4 decomposition: w(σ) sums over the sets P_i / groups.
   - L5 L3-condition: realized non-mono σ has ≥ 2 PMs in any all-nonzero
     solution.
   - Necessary conditions (a)(b)(c) — Prop 2 of the paper.

3. **Symmetry**: S₆ acts on colorings (vertex relabeling); (a)(b)(c) are
   invariant; the triple (P0,P1,P2) transforms by the same permutation.

4. **Computational certificates** (via `native_decide`; the boolean checks
   are simple and auditable):
   - C1: `allValidTriples` : List (Triple) — enumerate all nonempty
     pairwise edge-disjoint PM-subset triples; `native_decide : length =
     5610` and `no duplicates`.
   - C2: `reps : List Triple` — the 24 representatives (data transcribed
     from Appendix A of the paper; equality checked against the Python
     artifact by a checksum-comparison script outside Lean).
   - C3 (completeness): `native_decide : ∀ T ∈ allValidTriples,
     canon T ∈ reps`, where `canon` = min over the 720 perms of the
     lexicographic key. (5,610 × 720 canonicalizations in compiled code.)
   - C4 (elimination): `native_decide : ∀ rep ∈ reps, batchCheck rep`,
     where `batchCheck rep` enumerates all 10^F free-edge assignments and
     asserts each fails (no-new-mono) or (L3). (2,033,610 rows.)

5. **Glue theorem** (proof by contradiction): given col with wSol col,
   apply L1–L5 to get (a)(b)(c); take triple T of col; by C3, π·T ∈ reps;
   π·col has triple π·T and satisfies (a)(b)(c) (symmetry); its free-edge
   assignment is one of the enumerated rows, contradicting C4. ∎

## Trusted computing base

- Lean kernel type-checks the final theorem + the definitions of `batchCheck`,
  `canon`, `reps`, `allValidTriples` (the *statements* of C3/C4).
- The *values* of C3/C4 rest on the compiled evaluator (`native_decide`),
  whose code is the short boolean functions defined above; these are
  cross-checked OUTSIDE Lean against the independently audited Python
  implementations (audit/verification_2026-09-03/) and the z3 UNSAT runs.
  This matches community practice for computation-heavy certificates
  (and the formal-conjectures repo itself links external proofs).

## Transfer to formal-conjectures (Route B, after Route A)

- Clone google-deepmind/formal-conjectures; add our theorem to the
  MonochromaticQuantumGraph.lean family with `answer(True)` and the proof
  (their WeightsN/EqSystemN are over concrete domains; the ℚ route covers
  ℂ/ℝ/ℤ by field independence — needs a small transfer lemma per domain,
  plus a separate argument for trinary {−1,0,1} ⊆ ℤ).
- PR upstream (M. Krenn is the issue owner; DeepMind repo accepts PRs).

## Effort estimate

- Skeleton + data + IVC defs: ~300 lines.
- Reduction lemmas L1–L5: the meat, ~500–800 lines (Finset sums, products).
- Symmetry + glue: ~200 lines.
- C1–C4 executable checks: ~300 lines.
- Compile/run: C3/C4 need a few minutes of native code generation.

## Order of work

1. lake project skeleton + mathlib (needs toolchain; next session).
2. Data + C1/C2 + C3/C4 first (get the computation proven, validates the
   whole approach early).
3. L1–L5 + glue.
4. Route B.
