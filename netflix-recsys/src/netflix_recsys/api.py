"""REST API.

    uvicorn netflix_recsys.api:app --reload
    GET /recommend?title=Narcos&k=10&model=hybrid&diversity=0.3
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Query

from .data import load_catalog
from .models import MODEL_WEIGHTS, FeatureStore, TitleNotFound

ModelName = Literal["genre", "description", "lsa", "hybrid"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    store = FeatureStore(load_catalog(os.environ.get("NETFLIX_DATA")))
    app.state.store = store
    app.state.models = {name: store.model(name) for name in MODEL_WEIGHTS}
    yield


app = FastAPI(title="Netflix content-based recommender", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "titles": len(app.state.store.df), "models": list(app.state.models)}


@app.get("/titles")
def titles(q: str = Query(..., min_length=1), limit: int = Query(8, ge=1, le=25)) -> dict:
    """Fuzzy title search for autocomplete."""
    return {"query": q, "results": app.state.store.search(q, limit)}


@app.get("/recommend")
def recommend(
    title: str = Query(..., min_length=1),
    k: int = Query(10, ge=1, le=50),
    model: ModelName = "hybrid",
    diversity: float = Query(0.0, ge=0.0, le=0.9, description="MMR diversity; 0 = pure relevance"),
    content_type: Literal["Movie", "TV Show"] | None = None,
    explain: bool = True,
) -> dict:
    try:
        recs = app.state.models[model].recommend(
            title, k=k, diversity=diversity, content_type=content_type, explain=explain)
    except TitleNotFound as e:
        raise HTTPException(status_code=404, detail={"message": str(e), "suggestions": e.suggestions})
    return {"query": title, "model": model, "diversity": diversity,
            "results": [r.to_dict() for r in recs]}
