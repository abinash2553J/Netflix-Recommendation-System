# Spec: Evaluation Quality and Tie Handling

## Objective

Make recommendation ordering deterministic and the existing franchise-proxy evaluation transparent about uncertainty caused by exact score ties. Keep the current catalog, model features, and proxy labels. Results must repeat within the same installed environment; bit-for-bit equality across supported Python or dependency versions is not required.

## Scope and Decisions

- Resolve equal recommendation scores by title in case-insensitive A–Z order; this is a stable display tie-break, not relevance evidence.
- Preserve the current point metric fields (`franchise_hit@k`, `franchise_recall@k`, `franchise_mrr@k`) for compatibility. They use the deterministic display ordering.
- For ordinary similarity ranking (`diversity=0`), add best- and worst-case franchise metric bounds over all permutations of candidates with equal similarity scores:
  - `franchise_hit@{k}_tie_best`, `franchise_hit@{k}_tie_worst`
  - `franchise_recall@{k}_tie_best`, `franchise_recall@{k}_tie_worst`
  - `franchise_mrr@{k}_tie_best`, `franchise_mrr@{k}_tie_worst`
- For MMR reranking (`diversity>0`), bounds are not applicable because MMR changes ranking order using a diversity objective rather than similarity-score tie groups. Return `null` for the added bound fields on MMR evaluations; keep deterministic point metrics.
- A bound describes uncertainty from ties only. It does not quantify uncertainty in the heuristic franchise labels or establish personalized user satisfaction.

## Commands

Run from the repository root:

```powershell
python -m pytest -q
python scripts/run_eval.py
python scripts/tune_weights.py
```

`run_eval.py` regenerates `results/metrics.json` and `results/metrics.md`; `tune_weights.py` regenerates `results/tuning.json`.

## Project Structure

```text
src/netflix_recsys/models.py   → Deterministic ranking and MMR candidate ordering
src/netflix_recsys/evaluate.py → Point metrics and exact-tie metric bounds
tests/test_models.py          → Ranking tie-break behavior
tests/test_evaluate.py        → Tie-bound correctness and applicability
scripts/run_eval.py           → Generated report output
results/                      → Regenerated metric artifacts
README.md                      → User-facing summary and caveats
docs/portfolio-case-study.md  → Evaluation methodology and interpretation
```

## Code Style

Keep tie handling in the existing ranking and evaluation functions. Use exact score equality, matching the current exact boundary-tie diagnostic. The point ranking orders by descending score, then case-folded title ascending, with row index only as a final fallback for equal titles.

```python
ordered = np.lexsort((ids, title_keys[ids], -scores[ids]))
```

Use descriptive metric keys with explicit `_tie_best` / `_tie_worst` suffixes. Keep new calculations small and independently unit-tested.

## Testing Strategy

- Add focused unit tests for deterministic score ties, including ties that cross the top-k cutoff.
- Test best/worst Hit, Recall, and MRR bounds against hand-calculated score groups: a partial boundary tie, a fully included tie, and a relevant item ranked above the boundary.
- Verify MMR evaluations return null bounds and preserve point metrics.
- Run `python -m pytest -q`, regenerate both report sets, and confirm same-environment repeated runs produce identical result artifacts.
- No dependency changes or new datasets are in scope.

## Boundaries

- **Always:** Preserve existing metric keys; make equal-score app ordering deterministic; report tie bounds as proxy uncertainty; keep MMR bounds explicitly not applicable; preserve metric input and output contracts where possible.
- **Ask first:** Changing franchise proxy labels or split protocol; replacing current metrics; adding interaction/user-label data; adding dependencies; changing model features or MMR behavior beyond deterministic tie resolution.
- **Never:** Treat an alphabetical tie-break as relevance evidence; silently change proxy labels or metric definitions; claim user satisfaction from this dataset.

## Success Criteria

1. Equal-score recommendations are ordered case-insensitively by title A–Z, including deterministic selection when a tie crosses the requested result limit.
2. On non-MMR evaluation, tie-best and tie-worst fields are present for franchise Hit@k, Recall@k, and MRR@k, stay in `[0, 1]`, and bound the deterministic point metrics.
3. Bounds correctly cover all possible arrangements within exact-score tie groups, including cutoff ties and ties fully within top-k.
4. MMR evaluation preserves its point metrics and returns `null` for similarity-tie bounds.
5. Tests pass; repeated evaluation and tuning in the same installed environment generate byte-identical result artifacts.
6. README and case study explain the fields, their meaning, and why the bounds do not apply to MMR or measure user preference.

## Out of Scope

- Collecting human relevance judgments or new datasets.
- Replacing or changing the heuristic franchise proxy, tuning split, or model features.
- Requiring identical output across dependency or Python versions.
- Hosting or deployment work.
