# AUDIT ADDENDUM — D=4 / D=5 enumerations (2026-09-03)

Scope: the D=4 and D=5 exhaustive enumerations added on 2026-09-03
(compute_d45.py), which extend the audited D=3 result
(audit/AUDIT_REPORT_2026-09-03.md) to all color counts D >= 3 on n=6
simple graphs. Method identical to the D=3 audit: fresh independent
implementations, naive-reference filter replay, z3 independent backend.

## Results (all independent re-derivations)

| Check | D=4 | D=5 |
|---|---|---|
| raw class count | 2,160 (formula sum over audited triples) | 720 = 6 * 5! |
| orbit reps | 5, complete & non-redundant | 1 |
| batch rows | 4,917 (17^3 + 4 * 1) | 1 |
| naive-filter replay | 0 survivors, 0 filter disagreements | 0 survivors |
| z3 (b)+(c) | UNSAT 5/5 | UNSAT 1/1 |

## Notes

- IVC codes are TUPLES for D >= 4: the base-3 integer code used in the
  D=3 pipeline collides when digits reach 3 (3*3^v == 1*3^{v+1}). The
  D=4/5 implementation uses tuples throughout; this is a deliberate
  divergence from computation/*.py and is documented here.
- The elementary D <= 5 bound (3D <= 15) makes D=3,4,5 exhaustive; D >= 6
  has no solution trivially (each of D classes needs >= 3 disjoint
  edges). Verified by inspection; included in the paper as a lemma.
- First versions of the cross-check script had two scripting bugs
  (loading the 24-rep cache instead of the 5,610 raw triples; unequal
  class-padding widths across canonicalization calls). Both were
  identified and fixed; the stored reps and run results were unaffected
  (the full-list canonicalization always used the global padding).

## Verdict

PASS. The D=4 and D=5 no-solution claims are verified at the same level
of confidence as the D=3 claim: complete enumeration, sound filter
(three independent implementations agreeing), independent symbolic
confirmation.

Artifacts: audit/verification_2026-09-03/compute_d45.py,
indep_d45_check.py, d4_raw.pkl, d4_reps.pkl, d4_survivors.pkl,
d5_raw.pkl, d5_reps.pkl, d5_survivors.pkl.
Certificate: proof/certificate_d45.md.
