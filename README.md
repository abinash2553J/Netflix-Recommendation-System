# Netflix Content-Based Recommender

An interactive recommendation demo for Netflix titles, built with Python, scikit-learn, and Streamlit. It recommends similar titles using genres, plot descriptions (TF-IDF + latent semantic analysis), cast, and director information, with optional diversity reranking and explanations.

## Try the live demo

**Demo:** _Not deployed yet._ Follow the deployment steps below to publish it on Streamlit Community Cloud, then replace this line with the verified public URL.

## Run locally

Requires Python 3.10–3.12.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

python -m pip install -r requirements.txt
python -m streamlit run netflix-recsys/app/streamlit_app.py
```

Search for a title such as **Narcos**, choose the matching catalog entry, and adjust the model, number of results, content type, and diversity from the sidebar.

## Deploy the Streamlit demo

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
2. Select **Create app** and choose this repository and the `main` branch.
3. Set **Main file path** to `netflix-recsys/app/streamlit_app.py`.
4. In advanced settings, choose Python **3.12**.
5. Deploy. The repository-root `requirements.txt` installs the package and the dependencies required by the Streamlit app.
6. After the app starts, search for **Narcos** and confirm that a selected title and recommendations appear.
7. Replace the placeholder demo line above with the public URL only after the smoke test succeeds.

The catalog is read from `netflix-recsys/data/netflixData.csv`, committed with the project. Hosting should only proceed if you have the right to publish this data; confirm the original source and license and include any required attribution.

## REST API (optional, local or container)

The project also includes a FastAPI service:

```bash
cd netflix-recsys
python -m pip install -e ".[serve]"
uvicorn netflix_recsys.api:app --host 0.0.0.0 --port 8000
```

Then visit `http://localhost:8000/docs`. Useful endpoints are `/health`, `/titles?q=Narcos`, and `/recommend?title=Narcos`. A Dockerfile is included in `netflix-recsys/`.

## Tests

```bash
cd netflix-recsys
python -m pip install -e ".[dev]"
python -m pytest -q
```

A GitHub Actions workflow runs the tests on Python 3.10, 3.11, and 3.12.

## How it works

- **Genre:** TF-IDF over comma-separated genre labels.
- **Description:** stemmed unigram/bigram TF-IDF for plot similarity.
- **LSA:** a 150-dimensional truncated SVD representation of plot descriptions.
- **Cast and director:** sparse representations of shared talent.
- **Hybrid ranking:** a weighted combination of the feature blocks, with optional maximal marginal relevance (MMR) reranking for diversity.
- **Explanations:** shared genres, cast, and plot terms are shown with each recommendation.

The catalog contains no user viewing history or explicit ratings from users. Offline franchise-group metrics are a heuristic retrieval proxy, **not evidence of personalized user satisfaction**. See the [project documentation](netflix-recsys/README.md) and [evaluation spec](netflix-recsys/SPEC-evaluation-quality.md) for methodology and limitations.
