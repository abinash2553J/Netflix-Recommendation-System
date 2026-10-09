# Netflix Content-Based Recommender

A content-based recommender for 5,967 Netflix titles. It combines plot descriptions, genres, cast, directors, and latent semantic analysis (LSA), with optional maximal marginal relevance (MMR) reranking. Each recommendation includes an explanation of shared features.

**Portfolio focus:** build a sparse hybrid retrieval system, compare it with simpler baselines, and make the limits of offline recommendation evaluation explicit. The catalog has no user interactions, so this project does **not** claim to measure personalized user satisfaction.

## Try it locally

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
streamlit run app/streamlit_app.py
```

The Streamlit app opens locally. Search for a title such as `Narcos` to explore recommendations. To start the REST API instead:

```bash
uvicorn netflix_recsys.api:app --reload
```

Then open `http://localhost:8000/docs`. The API also provides `/recommend`, `/titles`, and `/health` endpoints. The Dockerfile runs the API on port 8000.

To regenerate evaluation artifacts:

```bash
python scripts/run_eval.py
python scripts/tune_weights.py
```

These commands write to `results/`. The `dev` extra includes `tabulate`, used to render the evaluation report.

## How recommendations are built

| Feature block | Representation | Role |
|---|---|---|
| Genre | TF-IDF with one token per comma-separated genre | Coarse category match |
| Description | Stemmed TF-IDF, unigrams and bigrams | Plot similarity |
| LSA | 150-dimensional TruncatedSVD projection of description vectors | Dense signal to help break ties |
| Cast and director | Binary TF-IDF over names | Talent and franchise overlap |

Each block is L2-normalized and scaled by the square root of its weight. As a result, one sparse dot product computes the weighted sum of block cosine similarities. The model scores one query at a time rather than building an all-pairs similarity matrix. Optional MMR reranking trades some relevance for more varied results.

## Evaluation snapshot

The checked-in results were regenerated with `python scripts/run_eval.py`. They measure retrieval of related titles in heuristic franchise groups, not whether a person would enjoy a recommendation.

| Model | Franchise Hit@10 (point; tie range) | Franchise MRR (point; tie range) | Boundary tie rate | Catalog coverage |
|---|---:|---:|---:|---:|
| Genre only | 0.206 (0.086–0.719) | 0.078 (0.023–0.706) | **0.970** | 0.346 |
| Description TF-IDF | 0.601 (0.601–0.601) | 0.454 (0.454–0.454) | 0.001 | 0.999 |
| LSA only | 0.222 (0.222–0.222) | 0.124 (0.124–0.124) | 0.002 | 0.996 |
| **Hybrid** | **0.809 (0.809–0.809)** | **0.728 (0.728–0.728)** | 0.002 | 0.996 |
| Hybrid + MMR 0.3 | 0.816 (N/A) | 0.732 (N/A) | 0.002 | 0.998 |
| Hybrid + MMR 0.5 | 0.790 (N/A) | 0.720 (N/A) | 0.002 | 0.998 |

The test set contains 690 query titles from 266 franchise groups. A separate weight-tuning script searches a small grid on one half of the groups and reports on the other: held-out franchise MRR is 0.725 for the tuned weights versus 0.600 for the hand-picked default. These are proxy results; details, ablations, and caveats are in the [portfolio case study](docs/portfolio-case-study.md).

For non-MMR rows, `results/metrics.json` also reports `_tie_best` and `_tie_worst` bounds for franchise Hit@10, Recall@10, and MRR@10. They show the range over possible orderings of equal-similarity items; the saved point metrics use title A–Z to resolve ties. MMR rows have `null` bounds (shown as N/A in `results/metrics.md`) because MMR reranks using diversity, not just similarity score. The bounds describe ranking ambiguity only, not uncertainty in the proxy labels.

### Important evaluation caveat

The genre-only model has identical scores at the top-10 boundary for about 97% of queries. When many results have equal scores, top-k membership depends on how those ties are ordered; its Hit@10 and MRR should therefore be read with their tie bounds, not as a reliable accuracy comparison. The hybrid's much lower tie rate makes its ranking more informative for this proxy, but it still does not establish user preference.

## Limitations and next experiment

- There are no user interactions or relevance labels; franchise membership is a heuristic proxy.
- Franchise groups favor titles with related names and shared cast, so the evaluation has its own bias.
- Catalog coverage and genre agreement are diagnostics; genre agreement is circular for models that use genre features.
- The descriptions are short, and the project does not use viewing history, popularity, or recency.
- The repository does not currently document the CSV's authoritative source or license. Confirm and add attribution and redistribution terms before publishing or redistributing the dataset.

A small human-labeled relevance set would be a better next step toward testing whether recommendations are useful to viewers. The [case study](docs/portfolio-case-study.md) describes this and other candidate experiments.

## Repository map

```text
src/netflix_recsys/   Data loading, text processing, models, evaluation, REST API
app/                  Streamlit demo
scripts/              Evaluation and weight-tuning commands
tests/                Unit and API tests
data/                 Netflix catalog CSV
results/              Generated metrics and tuning artifacts
docs/                 Portfolio case study
```
