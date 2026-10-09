# Case Study: Netflix Content-Based Recommender

## Summary

This project turns a genre-only title recommender into an explainable hybrid retrieval system for a catalog of 5,967 Netflix titles. It compares feature blocks and ranking variants using a franchise-retrieval proxy because the catalog contains no user interactions. The result is evidence about one retrieval task—not proof of personalized relevance or viewer satisfaction.

## Problem

The initial genre-only approach often returned many titles with identical similarity scores. In the current evaluation, 97.0% of queries have a tie between the tenth and eleventh result. A displayed top ten can therefore look precise even when the model cannot distinguish the boundary items.

The practical goal was to improve catalog discovery while surfacing why titles were recommended. The data does not contain ratings, clicks, or watch histories, so it cannot answer whether a particular person would like a result.

## Technical approach

The system builds five feature blocks:

- **Genre:** TF-IDF over comma-separated genres, kept as single tokens.
- **Description:** stemmed TF-IDF over unigrams and bigrams.
- **LSA:** a 150-dimensional TruncatedSVD representation of description vectors.
- **Cast and director:** binary TF-IDF over names.

Each block is normalized, then scaled by the square root of its weight. Concatenation lets a single sparse dot product represent the weighted sum of the per-block cosine similarities. The recommender scores a query against the catalog without constructing an all-pairs similarity matrix. MMR can optionally diversify the final list, and each result carries shared-feature explanations.

## Evaluation design

There is no behavioral ground truth in the dataset, so evaluation uses explicit proxies:

1. **Franchise retrieval:** titles grouped by a heuristic derived from their names should retrieve one another. The title itself is not a model feature. The current full-catalog evaluation uses 690 query titles across 266 groups.
2. **Boundary tie rate:** measures how often ranks 10 and 11 have equal scores, exposing whether the model can order results at the recommendation cutoff.
3. **Catalog coverage and genre diagnostics:** show which titles appear and how results relate by genre. Genre agreement is circular for models that use genre as an input.

For tuning, franchise groups are sorted and split deterministically by alternating groups. A small weight grid is selected on one half, and the selected weights are reported on the other half. This reduces direct group leakage into the reported tuning score, but the split and target are still based on the same heuristic franchise proxy.

Equal similarity scores are resolved for display in case-insensitive title A–Z order. For ordinary similarity ranking, the evaluator also reports best- and worst-case franchise Hit@k, Recall@k, and MRR@k across possible orderings of exactly tied scores. Existing point metrics are retained and use the deterministic display order. These bounds address ranking ambiguity only; they do not account for uncertainty or bias in the franchise proxy. Bounds are `null` for MMR because its diversity reranking does not define a single similarity-score ordering.

## Results

The table below is from the regenerated `results/metrics.md` and `results/metrics.json` artifacts. Scores are at k=10.

| Model | Franchise Hit@10 (point; tie range) | Franchise MRR (point; tie range) | Boundary tie rate | Catalog coverage |
|---|---:|---:|---:|---:|
| Genre only | 0.206 (0.086–0.719) | 0.078 (0.023–0.706) | 0.970 | 0.346 |
| Description TF-IDF | 0.601 (0.601–0.601) | 0.454 (0.454–0.454) | 0.001 | 0.999 |
| LSA only | 0.222 (0.222–0.222) | 0.124 (0.124–0.124) | 0.002 | 0.996 |
| Hybrid | 0.809 (0.809–0.809) | 0.728 (0.728–0.728) | 0.002 | 0.996 |
| Hybrid + MMR 0.3 | 0.816 (N/A) | 0.732 (N/A) | 0.002 | 0.998 |
| Hybrid + MMR 0.5 | 0.790 (N/A) | 0.720 (N/A) | 0.002 | 0.998 |

On the held-out half of the franchise groups, tuning improves franchise MRR from 0.600 for the hand-picked default weights to 0.725 for the selected weights; Hit@10 changes from 0.734 to 0.807. This indicates better retrieval of the chosen proxy, not a demonstrated improvement in what viewers prefer.

The ablation report suggests cast overlap contributes strongly to this franchise task: removing cast reduces MRR from 0.728 to 0.560. Removing LSA leaves MRR similar (0.728 to 0.729) but increases the boundary tie rate from 0.002 to 0.214. In this system, LSA's observed value is therefore more apparent in tie-breaking than in the franchise MRR score.

### Tie-related reproducibility note

The genre-only Hit@10/MRR point values use title A–Z tie resolution. Its boundary tie rate is about 0.970, so the best/worst bounds in `results/metrics.json` are more informative than the point values alone. During the audit, those metrics changed between artifact generations while the tie rate remained about the same; this confirms that tie ordering materially affects the proxy scores.

## Limitations

- The dataset contains no user feedback, so there is no ground truth for personal taste.
- The franchise labels are inferred from title strings. The proxy favors title-adjacent relationships and shared cast, and groups may be noisy.
- Feature choices and tuning are evaluated against that same proxy; the held-out group split reduces but does not eliminate proxy bias.
- Genre agreement is circular for genre-informed models, and catalog coverage does not measure relevance.
- Short descriptions limit the signal available to text features.
- The repository currently has no authoritative source or license information for `data/netflixData.csv`. Its provenance and redistribution terms must be confirmed before making attribution or licensing claims.

## Next experiments

1. Create a small, documented human-labeled relevance set spanning several query types, then compare the proxy rankings with human judgments.
2. Evaluate a sentence-embedding feature block against the same fixed queries and labels, if those labels become available.
3. If user interaction data is obtained with appropriate rights, test collaborative filtering and a hybrid with user- and item-level ranking metrics.

## Reproduction

From the repository root:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python scripts/run_eval.py
python scripts/tune_weights.py
streamlit run app/streamlit_app.py
```

The evaluation scripts regenerate the artifacts under `results/`. `tabulate` is included in the development extra because the evaluation report uses pandas' Markdown table rendering.
