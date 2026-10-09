# Spec: Reproducible Project Story

## Objective

Make the existing Netflix content-based recommender understandable and reproducible for data scientist and ML engineer hiring managers. A reviewer should quickly understand the problem, the system, the evidence behind its results, its limitations, and how to run it locally. The documentation should also give the project owner a concise, evidence-based case study for technical interviews.

This module documents the current system and its verified behavior. Changes to evaluation methodology and public hosting belong to the separate `evaluation-quality` and `hosted-demo` modules.

## Assumptions

1. The current Netflix catalog, recommender, Streamlit app, API, evaluation scripts, and tests are the project baseline.
2. Existing metric values and project claims must be checked against the repository artifacts and executable commands before being presented as facts.
3. The project remains focused on Netflix recommendations; no unrelated dataset or product scope is introduced in this module.
4. Existing project commands and technology choices are retained unless verification shows they are incorrect.

## Tech Stack

- Python 3.10 or newer, per `pyproject.toml`
- pandas, NumPy, SciPy, scikit-learn, NLTK, and RapidFuzz for recommendation and data processing
- pytest for tests
- FastAPI and Uvicorn for the REST API
- Streamlit for the interactive demo

Exact installed package versions are not part of this documentation module's contract.

## Commands

Run from the repository root:

```powershell
python -m pip install -e ".[dev]"
pytest -q
python scripts/run_eval.py
python scripts/tune_weights.py
uvicorn netflix_recsys.api:app --reload
streamlit run app/streamlit_app.py
```

The commands must be verified against the supported setup instructions before publication. Evaluation and tuning commands may take longer than tests and may update files under `results/`.

## Project Structure

```text
README.md                     → Project overview, verified results, quick start
docs/portfolio-case-study.md  → Interview-oriented problem, decisions, evidence, and limitations
src/netflix_recsys/           → Data loading, text processing, models, API, evaluation
app/streamlit_app.py          → Streamlit demo
scripts/                      → Evaluation and weight-tuning entry points
tests/                        → Automated tests
data/                         → Netflix catalog used by the project
results/                      → Generated evaluation and tuning artifacts
```

## Code Style

This module is documentation-only. Any code snippets in the documentation must match the existing public API and style; for example, the existing usage pattern is:

```python
from netflix_recsys import FeatureStore, load_catalog

store = FeatureStore(load_catalog())
model = store.model("hybrid")
for recommendation in model.recommend("Narcos", k=5, diversity=0.3):
    print(recommendation.title, recommendation.score, recommendation.why)
```

Use concise Markdown, descriptive headings, fenced code blocks with language identifiers, and explicit distinctions between measured results, proxy metrics, and limitations. Do not claim that franchise retrieval or genre agreement proves personal relevance or user satisfaction.

## Testing Strategy

- Run the existing test suite with `pytest -q` after documentation changes that alter commands, APIs, or behavior descriptions.
- Run the documented evaluation command and verify every published metric against its generated output before changing metric claims.
- Follow the documented quick start from a clean Python environment and confirm the demo can load the checked-in catalog.
- Check links and commands in the README and case study manually; no new documentation-testing dependency is in scope.

## Boundaries

- **Always:** Keep setup instructions executable; distinguish proxy evaluation from user-level recommendation quality; ground all quantitative claims in generated artifacts; state important limitations and data provenance accurately.
- **Ask first:** Changing the model or evaluation methodology; adding datasets or dependencies; changing CI/deployment configuration; publishing or redistributing data where its license or provenance is unclear.
- **Never:** Invent results, present proxy metrics as user satisfaction, commit credentials, or silently remove existing tests or evaluation claims.

## Success Criteria

1. The README explains the recommendation problem, the approach, the main verified result, the evaluation caveat, and how to run the project without requiring a reviewer to inspect source files first.
2. A linked case study describes the problem, key technical decisions, evaluation design, measured outcomes, limitations, and a reasonable next experiment.
3. Every reported quantitative result in the README and case study matches a checked-in generated result or a documented reproducible command; unsupported claims are removed or qualified.
4. A reviewer can install the project, run the tests and evaluation, and launch the local demo using the documented commands from the repository root.
5. The writing clearly states that the dataset lacks user interactions and that the current evaluation proxies do not establish personalized user satisfaction.
6. Documentation does not require unrelated product features, a model rewrite, or a new data source.

## Open Questions

- What is the authoritative source and license for `data/netflixData.csv`, and what attribution or redistribution notice should the project provide?
- Which hosting provider should the separate `hosted-demo` module target?
