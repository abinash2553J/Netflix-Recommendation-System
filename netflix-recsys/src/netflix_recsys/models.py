"""Feature extraction and the recommender.

Design notes
------------
* Every feature block is L2-normalised. Concatenating blocks scaled by ``sqrt(weight)``
  makes a single dot product equal to the *weighted sum of per-block cosine similarities*,
  so a hybrid model needs one sparse matrix and no N x N similarity matrix.
* Similarities are computed per query (one sparse mat-vec), so memory stays O(N * features)
  instead of O(N^2).
* Titles with the same name as the query are never returned (no self match, no duplicates).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from .text import clean, split_list

# Block weights per model. Weights are relative; they are normalised to sum to 1.
MODEL_WEIGHTS: dict[str, dict[str, float]] = {
    "genre": {"genre": 1.0},
    "description": {"desc": 1.0},
    "lsa": {"lsa": 1.0},
    # tuned with scripts/tune_weights.py on half of the franchise groups, checked on the other half
    "hybrid": {"genre": 0.25, "desc": 0.45, "lsa": 0.05, "cast": 0.20, "director": 0.05},
}


class TitleNotFound(KeyError):
    def __init__(self, title: str, suggestions: list[str]):
        super().__init__(title)
        self.title = title
        self.suggestions = suggestions

    def __str__(self) -> str:
        hint = f" Did you mean: {', '.join(self.suggestions)}?" if self.suggestions else ""
        return f"Title not found: {self.title!r}.{hint}"


@dataclass
class Recommendation:
    title: str
    content_type: str
    genres: str
    year: int | None
    imdb: float | None
    score: float
    description: str
    why: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class FeatureStore:
    """Fits all feature blocks once; models are cheap views over these blocks."""

    def __init__(self, df: pd.DataFrame, stem: bool = True, lsa_dims: int = 150, random_state: int = 0):
        self.df = df.reset_index(drop=True)
        self.stem = stem
        n = len(self.df)

        desc_clean = self.df["Description"].map(lambda t: clean(t, stem=stem))
        genre_vec = TfidfVectorizer(tokenizer=split_list, token_pattern=None, lowercase=False)
        cast_vec = TfidfVectorizer(tokenizer=split_list, token_pattern=None, lowercase=False,
                                   min_df=2, binary=True)
        dir_vec = TfidfVectorizer(tokenizer=split_list, token_pattern=None, lowercase=False,
                                  min_df=2, binary=True)
        desc_vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)

        desc = desc_vec.fit_transform(desc_clean)
        svd = TruncatedSVD(n_components=min(lsa_dims, desc.shape[1] - 1, n - 1), random_state=random_state)
        lsa = svd.fit_transform(desc)

        self.blocks: dict[str, sparse.csr_matrix] = {
            "genre": normalize(genre_vec.fit_transform(self.df["Genres"])).tocsr(),
            "cast": normalize(cast_vec.fit_transform(self.df["Cast"])).tocsr(),
            "director": normalize(dir_vec.fit_transform(self.df["Director"])).tocsr(),
            "desc": normalize(desc).tocsr(),
            "lsa": sparse.csr_matrix(normalize(lsa)),
        }

        # Un-stemmed unigram TF-IDF, used only to explain recommendations in readable words.
        self._terms_vec = TfidfVectorizer(stop_words="english", min_df=2, sublinear_tf=True)
        self._terms = self._terms_vec.fit_transform(self.df["Description"].str.lower()).tocsr()
        self._terms_names = np.asarray(self._terms_vec.get_feature_names_out())

        self._genre_sets = [set(split_list(g)) for g in self.df["Genres"]]
        self._cast_sets = [set(split_list(c)) for c in self.df["Cast"]]

        lowered = self.df["Title"].str.lower()
        self._lower_titles = lowered.tolist()
        self._same_title: dict[str, np.ndarray] = {
            t: np.flatnonzero(lowered.to_numpy() == t) for t in lowered.unique()
        }
        self._first_idx: dict[str, int] = {t: int(ix[0]) for t, ix in self._same_title.items()}
        self._title_keys = self.df["Title"].str.casefold().to_numpy()

    # ---- lookup ---------------------------------------------------------------------
    def search(self, query: str, limit: int = 8) -> list[str]:
        """Fuzzy title search (used for autocomplete and 'did you mean')."""
        q = query.lower().strip()
        if not q:
            return []
        hits = process.extract(q, self._lower_titles, scorer=fuzz.WRatio, limit=limit * 3)
        seen, out = set(), []
        for _, _, i in hits:
            title = self.df.at[i, "Title"]
            if title not in seen:
                seen.add(title)
                out.append(title)
            if len(out) == limit:
                break
        return out

    def resolve(self, title: str) -> int:
        key = title.lower().strip()
        if key in self._first_idx:
            return self._first_idx[key]
        raise TitleNotFound(title, self.search(title, 3))

    def model(self, name: str = "hybrid", weights: dict[str, float] | None = None) -> "Recommender":
        w = weights if weights is not None else MODEL_WEIGHTS[name]
        return Recommender(self, w, name=name)

    # ---- explanations ---------------------------------------------------------------
    def explain(self, i: int, j: int, n_terms: int = 4) -> dict:
        shared_terms: list[str] = []
        prod = self._terms[i].multiply(self._terms[j]).tocoo()
        if prod.nnz:
            order = np.argsort(-prod.data)[:n_terms]
            shared_terms = [str(self._terms_names[prod.col[o]]) for o in order]
        return {
            "shared_genres": sorted(self._genre_sets[i] & self._genre_sets[j]),
            "shared_cast": [c.title() for c in sorted(self._cast_sets[i] & self._cast_sets[j])],
            "shared_terms": shared_terms,
        }


class Recommender:
    def __init__(self, store: FeatureStore, weights: dict[str, float], name: str = "custom"):
        total = float(sum(weights.values()))
        self.store = store
        self.name = name
        self.weights = {k: v / total for k, v in weights.items()}
        self.X = sparse.hstack(
            [np.sqrt(w) * store.blocks[b] for b, w in self.weights.items()], format="csr"
        )

    # ---- scoring --------------------------------------------------------------------
    def scores_for(self, idx: int) -> np.ndarray:
        s = (self.X @ self.X[idx].T).toarray().ravel()
        s[self.store._same_title[self.store._lower_titles[idx]]] = -np.inf
        return s

    def score_chunk(self, rows: np.ndarray) -> np.ndarray:
        """Dense similarities for a chunk of query rows (used by the evaluator)."""
        s = (self.X[rows] @ self.X.T).toarray()
        for r, q in enumerate(rows):
            s[r, self.store._same_title[self.store._lower_titles[q]]] = -np.inf
        return s

    # ---- recommendation -------------------------------------------------------------
    def recommend_idx(self, idx: int, k: int = 10, diversity: float = 0.0,
                      content_type: str | None = None, pool: int = 50) -> tuple[np.ndarray, np.ndarray]:
        s = self.scores_for(idx)
        if content_type:
            s[(self.store.df["Content Type"] != content_type).to_numpy()] = -np.inf
        return self.rank(s, k, diversity, pool)

    def rank(self, s: np.ndarray, k: int, diversity: float = 0.0, pool: int = 50) -> tuple[np.ndarray, np.ndarray]:
        n = max(k, pool) if diversity > 0 else k
        finite = np.flatnonzero(np.isfinite(s))
        n = min(n, len(finite))
        if n == 0:
            return np.array([], dtype=int), np.array([], dtype=s.dtype)
        cutoff = np.partition(s[finite], len(finite) - n)[len(finite) - n]
        above = finite[s[finite] > cutoff]
        tied = finite[s[finite] == cutoff]
        tied = tied[np.argsort(self.store._title_keys[tied], kind="stable")]
        top = np.concatenate((above, tied[:n - len(above)]))
        top = top[np.lexsort((top, self.store._title_keys[top], -s[top]))]
        if diversity > 0 and len(top) > k:
            top = self._mmr(top, s[top], k, lam=1.0 - diversity)
        top = top[:k]
        return top, s[top]

    def _mmr(self, cand: np.ndarray, rel: np.ndarray, k: int, lam: float) -> np.ndarray:
        """Maximal marginal relevance: trade relevance against similarity to already-picked items."""
        sims = (self.X[cand] @ self.X[cand].T).toarray()
        chosen = [0]
        rest = list(range(1, len(cand)))
        while rest and len(chosen) < k:
            best = max(rest, key=lambda i: lam * rel[i] - (1 - lam) * sims[i, chosen].max())
            chosen.append(best)
            rest.remove(best)
        return cand[chosen]

    def recommend(self, title: str, k: int = 10, diversity: float = 0.0,
                  content_type: str | None = None, explain: bool = True) -> list[Recommendation]:
        idx = self.store.resolve(title)
        ids, scores = self.recommend_idx(idx, k, diversity, content_type)
        df = self.store.df
        out = []
        for j, sc in zip(ids, scores):
            row = df.iloc[j]
            out.append(Recommendation(
                title=row["Title"], content_type=row["Content Type"], genres=row["Genres"],
                year=None if pd.isna(row["Year"]) else int(row["Year"]),
                imdb=None if pd.isna(row["Imdb"]) else float(row["Imdb"]),
                score=round(float(sc), 4), description=row["Description"],
                why=self.store.explain(idx, int(j)) if explain else {},
            ))
        return out
