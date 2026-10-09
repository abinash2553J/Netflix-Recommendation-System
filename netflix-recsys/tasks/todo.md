# Reproducible Project Story Tasks

## Phase 1: Evidence and Documentation

- [x] **Task 1: Audit current claims, commands, and data provenance**
  - Acceptance: Every quantitative claim is traceable to a generated artifact or reproducible command; documented commands are checked against project behavior; dataset provenance/license is supported by evidence or marked unresolved.
  - Verify: `python -m pytest -q` passed (18 tests); evaluation and tuning scripts completed after adding the missing report dependency and refreshed outputs; dataset metadata and repository references contained no source or license.
  - Files: `pyproject.toml`, `results/metrics.json`, `results/metrics.md`, `results/tuning.json`.
  - Dependencies: None.

- [x] **Task 2: Update the README for a portfolio reviewer**
  - Acceptance: README explains the problem, approach, verified result, evaluation caveat, setup, and local run path; links to the case study; contains no unsupported numerical or data-license claims.
  - Verify: Check all commands, figures, and links against Task 1 evidence and repository paths.
  - Files: `README.md`.
  - Dependencies: Task 1.

- [x] **Task 3: Write the interview-ready case study**
  - Acceptance: New case study covers problem, technical choices, evaluation design, measured outcomes, limitations, and a justified next experiment; all claims are evidenced and proxy metrics are not described as personalized satisfaction.
  - Verify: Cross-check each figure against `results/metrics.json`, `results/metrics.md`, or `results/tuning.json`; inspect Markdown links and terminology.
  - Files: `docs/portfolio-case-study.md`.
  - Dependencies: Task 1.

## Checkpoint: Documentation Review

- [x] Confirm all numeric claims are traceable and limitations are clear.
- [x] Have the project owner review the README and case study before final environment verification.

## Phase 2: Reproducibility Verification

- [x] **Task 4: Verify documented local setup and end-to-end commands**
  - Acceptance: Documented installation, tests, evaluation, tuning, and local demo launch work in a clean or isolated environment, or limitations are stated accurately; no unrelated application/deployment changes are made.
  - Verify: In a clean Python 3.11 virtual environment, editable install, 18 tests, evaluation, tuning, a recommendation query (`Narcos` returned three results), and Streamlit HTTP 200 all passed.
  - Files: `README.md`, `docs/portfolio-case-study.md`.
  - Dependencies: Tasks 2 and 3.

## Checkpoint: Complete

- [x] All `SPEC-reproducible-story.md` success criteria are met.
- [x] Project owner reviewed and approved the completed module before work began on this dependent module.

## Evaluation-Quality Module

- [x] **Drafting `SPEC-evaluation-quality.md`**
  - Acceptance: Confirmed intent captured: stable title A–Z display ties, exact tie bounds for ordinary rankings, MMR bounds marked not applicable, and same-environment reproducibility.
  - Verify: Spec checked against the agreed scope before implementation.
  - Files: `SPEC-evaluation-quality.md`.
  - Dependencies: Completed `reproducible-story` module.

- [x] **Making recommendation score ties deterministic**
  - Acceptance: Equal finite scores sort by case-insensitive title A–Z, with deterministic cutoff selection; MMR candidate processing inherits that stable order.
  - Verify: `tests/test_models.py` covers tied candidates crossing the requested top-k boundary.
  - Files: `src/netflix_recsys/models.py`, `tests/test_models.py`.
  - Dependencies: Spec.

- [x] **Adding franchise metric tie bounds**
  - Acceptance: Existing point metrics remain; ordinary ranking adds best/worst Hit, Recall, and MRR bounds; MMR results return null bounds.
  - Verify: Focused tests cover hand-calculated cases and exhaustive permutations of tied groups; full tests pass.
  - Files: `src/netflix_recsys/evaluate.py`, `tests/test_evaluate.py`.
  - Dependencies: Deterministic ranking behavior.

- [x] **Documenting and reproducing tie-aware results**
  - Acceptance: Generated Markdown renders MMR bounds as N/A; README and case study explain the point ordering, bounds, and MMR limitation; result artifacts are identical on repeated same-environment runs.
  - Verify: `python -m pytest -q` (24 passed); `run_eval.py` and `tune_weights.py` each run twice with byte-identical JSON/Markdown outputs; documented figures were cross-checked against artifacts.
  - Files: `scripts/run_eval.py`, `results/metrics.json`, `results/metrics.md`, `results/tuning.json`, `README.md`, `docs/portfolio-case-study.md`.
  - Dependencies: Tie-bound evaluation.
