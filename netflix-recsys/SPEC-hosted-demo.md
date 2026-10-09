# Spec: Public Streamlit Demo

## Objective

Make the existing Netflix recommender usable by portfolio reviewers through a public Streamlit Community Cloud URL. The hosted app should preserve the current local Streamlit experience and load the catalog included with the project. The project owner confirmed that the catalog is cleared for public hosting.

This module prepares, documents, deploys, and smoke-tests the existing Streamlit app. It does not replace the UI, host the REST API, or add recommendation features.

## Tech Stack

- Python, using a supported version allowed by `pyproject.toml`
- Existing Streamlit app at `app/streamlit_app.py`
- Existing runtime dependencies in `pyproject.toml`
- Streamlit Community Cloud, with source connected from GitHub

No new application dependency is planned. Deployment dependencies should use the `serve` extra rather than installing test and development-only packages.

## Commands

Run locally from the repository root:

```powershell
python -m pip install -e ".[serve]"
streamlit run app/streamlit_app.py
```

Run the existing automated tests before deployment:

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
```

Deployment is initiated through the Streamlit Community Cloud interface by connecting the GitHub repository, selecting `app/streamlit_app.py` as the entry point, and using the supported Python version configured for the app. The final public URL is recorded in the README after a successful smoke test.

## Project Structure

```text
app/streamlit_app.py  → Existing interactive recommender UI
src/netflix_recsys/   → Recommendation logic and local catalog loading
data/                 → Catalog confirmed as cleared for public hosting
pyproject.toml        → Runtime and development dependency definitions
requirements.txt      → Streamlit Cloud install entry, using runtime dependencies
README.md             → Public demo link and deployment notes
tests/                → Existing automated test suite
```

## Code Style

Keep the existing Streamlit app and recommendation API. Configure the deployment to point to the current entry point rather than creating a second UI:

```powershell
streamlit run app/streamlit_app.py
```

Use existing package extras and repo conventions. Do not duplicate runtime dependencies in a separate list unless the hosting provider requires a format not already supported by the project.

## Testing Strategy

- Run `python -m pytest -q` before deployment.
- Confirm the configured runtime dependencies install in a clean environment without development/test packages.
- Deploy from the GitHub repository and confirm the public URL loads.
- Smoke-test title search and recommendations with a known title such as `Narcos`; confirm the page shows the selected title and recommendation results.
- Check provider logs if deployment or catalog loading fails; do not suppress errors or report deployment success without a live smoke test.

## Boundaries

- **Always:** Use the existing Streamlit UI; load the committed catalog using the existing loader; keep credentials and deployment tokens out of source control; state any hosting sleep/cold-start behavior accurately; only publish after the owner-confirmed data clearance.
- **Ask first:** Creating or making a GitHub repository public; changing repository visibility; adding billing or a paid hosting plan; collecting analytics or user data; adding secrets or external services; changing the app's behavior or visual design.
- **Never:** Commit secrets; expose data beyond the owner-confirmed clearance; claim a public demo is live without verifying its URL; add tracking or user data collection without approval.

## Success Criteria

1. Streamlit Community Cloud can install the runtime dependencies using the repository's deployment dependency file.
2. The deployed app is reachable at a stable public URL and loads the existing recommender UI.
3. Searching for `Narcos` produces a selected title and recommendation results in the hosted app.
4. README links directly to the verified public demo and explains any relevant cold-start or availability caveat.
5. Existing tests pass and the documented local command continues to work.
6. No credentials, tracking, unrelated app features, or REST API hosting are introduced.

## Open Questions

- Is there an existing GitHub repository for this project that can be connected to Streamlit Community Cloud, or does one need to be created?
- What dataset attribution/source should be displayed, if any, despite the owner's confirmation that public hosting is permitted?
- What public-facing project title and short app description should be used in the hosting listing? Default to the current project title and README summary if the owner has no preference.
