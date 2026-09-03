# Krenn–Gu Conjecture — Research OS

Bounty: €3,000 (Dominik Leitner + Mario Krenn) for the FIRST proof **or**
verifiable counterexample of the Krenn–Gu conjecture (inherited vertex
coloring / monochromatic graphs). Status as of 2026-08-27: OPEN, unclaimed.

Target (modern graph-theoretic form): μ(G) ≤ 2 for every graph G with
|V(G)| > 4 (μ = matching index; μ(K₄) = 3 is the sole known exception).
Equivalently: for even n ≥ 6 and d ≥ 3, no bi-colored weighted graph
(multigraph, complex weights, bichromatic edges allowed) has all d
monochromatic inherited vertex colorings of unit weight with all other
colorings cancelling.

Acceptance conditions: solution must appear in a respected peer-reviewed
journal; counterexamples must be confirmable (e.g. via software).
No deadline. Judge: Mario Krenn.

Research OS rules (non-negotiable):
- PRODUCED != AUDITED; COMPUTATION != PROOF;
  REPAIRED != INDEPENDENTLY_REAUDITED; READY != AUTHORIZED.
- A valid LRAT/Lean certificate certifies only its exact statement —
  not the mathematical encoding, weight reduction, or the full conjecture.
- Restrictions matter: simple vs multigraph; monochromatic-only vs
  bichromatic edges; positive-real / real / complex weights. Never
  inherit a restricted theorem as unconditional.
- Do not optimize for an affirmative proof. Valid terminal states:
  PROVED / DISPROVED / PARTIAL / BLOCKED / UNKNOWN.

State and ledgers: research_os/RESEARCH_STATE.md (canonical snapshot),
research_os/CLAIM_LEDGER.yaml, research_os/APPROACH_REGISTRY.yaml,
research_os/GATES.yaml, research_os/ARTIFACT_MANIFEST.json.
Source index: sources/SOURCE_INDEX.md.
Workspace: proof/ counterexample/ computation/ audit/ archive/.

Current phase: KG-P0 FRONTIER RECONSTRUCTION (complete 2026-08-27).
KG-P1 is proposed in RESEARCH_STATE.md but NOT authorized — requires
explicit GO from the user.
