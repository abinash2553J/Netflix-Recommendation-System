# Implementation Plan: Reproducible Project Story

## Overview

Deliver the approved `reproducible-story` module from `SPEC-reproducible-story.md`: make the current Netflix recommender easy to understand, evaluate from its existing evidence, run locally, and discuss in an interview. This is a documentation and verification effort; it does not change the model, evaluation methodology, data, or hosting configuration.

## Architecture Decisions

- Preserve the existing README as the repository entry point and add one focused case study at `docs/portfolio-case-study.md`.
- Treat generated artifacts under `results/` as the quantitative source of truth; rerun the evaluation commands before documenting metrics.
- Keep franchise retrieval, catalog coverage, genre agreement, and tie rate explicitly framed as proxy or diagnostic measures, not personalized user-satisfaction evidence.
- Do not invent dataset attribution or licensing. Resolve provenance before making redistribution or licensing claims.
- Keep hosting-provider selection and deployment work in the separate `hosted-demo` module.

## Task List

### Phase 1: Evidence and Documentation

- [x] Task 1: Audit current claims, commands, and data provenance
- [x] Task 2: Update the README for a portfolio reviewer
- [x] Task 3: Write the interview-ready case study

### Checkpoint: Documentation Review

- [x] All quantitative claims are traceable to generated results.
- [x] README and case study explain the proxy nature and limitations of the evaluation.
- [x] Project owner reviews and approves the documentation before final reproducibility checks.

### Phase 2: Reproducibility Verification

- [x] Task 4: Verify documented local setup and end-to-end commands

### Checkpoint: Complete

- [x] Documented installation, tests, evaluation, and local demo launch have been verified.
- [x] All success criteria in `SPEC-reproducible-story.md` are met.
- [ ] Project owner reviews the completed module before planning dependent modules.

## Task Details

### Task 1: Audit current claims, commands, and data provenance

**Description:** Compare README claims and command examples with source behavior, tests, `results/metrics.json`, `results/metrics.md`, and `results/tuning.json`. Execute the documented tests and evaluation/tuning commands where feasible, record any discrepancies, and identify available evidence for the catalog's source and license.

**Acceptance criteria:**
- [x] Every quantitative claim intended for the README or case study has a traceable artifact or command.
- [x] Run commands are checked against `pyproject.toml`, entry points, data loading, and API behavior.
- [x] Data provenance and licensing are either supported by repository evidence or explicitly recorded as unresolved; no attribution is guessed.

**Verification:**
- [x] Run `python -m pytest -q` in the configured project environment (18 passed).
- [x] Run `python scripts/run_eval.py` and `python scripts/tune_weights.py`; refresh generated results and compare values to prior artifacts.
- [x] Inspect the dataset metadata or existing project references; source/license is not documented and remains an open question.

**Dependencies:** None  
**Files touched:** `pyproject.toml`, `results/metrics.json`, `results/metrics.md`, and `results/tuning.json`.  
**Estimated scope:** Medium

### Task 2: Update the README for a portfolio reviewer

**Description:** Reshape `README.md` into a concise reviewer-facing entry point that explains the recommendation problem, core technical approach, verified evidence, key caveat, quick start, and links to the case study and runnable demo/API.

**Acceptance criteria:**
- [x] A reviewer can identify the problem, approach, main verified result, and evaluation caveat from the README without inspecting source files.
- [x] Setup and run commands match the verified environment and repository behavior.
- [x] Quantitative claims are supported by Task 1 evidence, and no proxy is presented as personal relevance or satisfaction.
- [x] README links to `docs/portfolio-case-study.md`; unsupported data attribution or licensing claims are absent.

**Verification:**
- [x] Check commands against the results of Task 1.
- [x] Review all numeric values and links in the README against checked-in artifacts and repository paths.

**Dependencies:** Task 1  
**Files likely touched:**
- `README.md`

**Estimated scope:** Small

### Task 3: Write the interview-ready case study

**Description:** Add `docs/portfolio-case-study.md` describing the problem framing, relevant technical decisions, evaluation design, measured outcomes, limitations, and a justified next experiment. Reuse the evidence audit rather than creating or changing an evaluation methodology.

**Acceptance criteria:**
- [x] Case study covers problem, system choices, evaluation protocol, results, limitations, and a next experiment.
- [x] All quantitative claims are traceable to Task 1 evidence and their interpretation is appropriately qualified.
- [x] Clearly states that the dataset lacks user interactions and the current proxies do not establish personalized user satisfaction.
- [x] Does not claim unresolved data provenance or licensing details as fact.

**Verification:**
- [x] Independently cross-check each number and interpretation against `results/metrics.json`, `results/metrics.md`, or `results/tuning.json`.
- [x] Check Markdown links and terminology against README and source.

**Dependencies:** Task 1  
**Files likely touched:**
- `docs/portfolio-case-study.md`

**Estimated scope:** Small

### Task 4: Verify documented local setup and end-to-end commands

**Description:** Follow the README from a clean or isolated Python environment to verify installation, tests, evaluation, and local demo launch. Fix documentation mismatches; if an actual application defect blocks the documented path, stop and ask before expanding this documentation module into code changes.

**Acceptance criteria:**
- [x] Installation and documented commands work from the repository root in a clean Python 3.11 environment.
- [x] Tests pass and evaluation outputs are reproducible enough to support published claims; genre-only tie instability is disclosed.
- [x] The Streamlit app starts and loads the checked-in catalog; HTTP responds successfully and a real recommendation query returns three results.
- [x] No unrelated code, model, evaluation-method, dataset, or deployment changes are introduced.

**Verification:**
- [x] Use a clean virtual environment with the documented install command.
- [x] Run `python -m pytest -q`, `python scripts/run_eval.py`, and `python scripts/tune_weights.py`.
- [x] Run `streamlit run app/streamlit_app.py` and confirm the local page responds and can produce recommendations.
- [x] Recheck README and case-study commands and claims after documentation corrections.

**Dependencies:** Tasks 2 and 3  
**Files likely touched:** `README.md`, `docs/portfolio-case-study.md`  
**Estimated scope:** Medium

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Dataset source or license cannot be established from repository evidence | High for public redistribution/attribution | Do not invent attribution or license; keep the issue open and request owner input before publishing claims or changing data distribution. |
| Existing metrics differ from checked-in artifacts or reruns | Medium | Use the actual reproducible output as source of truth and explain environment-dependent variation rather than silently retaining stale values. |
| Genre-only Hit@10 and MRR shift between runs while its boundary tie rate remains about 0.970 | High for interpreting the baseline | Report the tie rate and explain that arbitrary ordering among tied scores makes the genre-only top-k proxy metrics unstable; do not interpret the raw change as model improvement. |
| A documented run command fails due to environment or packaging assumptions | Medium | Verify in an isolated environment; correct instructions first and ask before expanding scope to code changes. |
| Existing README combines evaluation findings with project overview | Low | Keep the README concise and move detailed evidence and interpretation into the linked case study. |

## Open Questions

- What is the authoritative source and license for `data/netflixData.csv`, and what attribution or redistribution notice should the project provide?
- Which hosting provider should the separate `hosted-demo` module target? This is tracked in its spec, not a decision required to execute this module.
