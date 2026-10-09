"""Catalog loading."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "netflixData.csv"

TEXT_COLS = ["Title", "Description", "Genres", "Cast", "Director", "Production Country", "Content Type"]


def load_catalog(path: str | Path | None = None) -> pd.DataFrame:
    """Load the Netflix catalog.

    Rows without a title, description or genre are dropped (none in the shipped CSV, but
    the guard keeps the pipeline safe). The index is reset so that DataFrame labels are
    equal to row positions, which the similarity code relies on.
    """
    df = pd.read_csv(path or DEFAULT_PATH)
    df = df.dropna(subset=["Title", "Description", "Genres"]).reset_index(drop=True)
    for col in TEXT_COLS:
        if col in df:
            df[col] = df[col].fillna("").astype(str)
    df["Year"] = pd.to_numeric(df["Release Date"], errors="coerce").astype("Int64")
    df["Imdb"] = pd.to_numeric(df["Imdb Score"].astype(str).str.split("/").str[0], errors="coerce")
    return df
