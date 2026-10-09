"""Offline evaluation.

The Netflix CSV has no user interactions, so there is no ground truth for "what would a
viewer like". We use three proxy signals and are explicit about what each one can and
cannot tell you:

* **Franchise retrieval** (Hit@k, Recall@k, MRR): titles that share a franchise name
  ("Narcos", "Narcos: Mexico") should retrieve each other. No model uses the title as a
  feature, so this is a fair test for every model.
* **Genre agreement / diversity / type match**: *circular* for models that use genres as a
  feature (they are optimised for it), but informative for description-only models.
* **Catalog coverage, boundary ties**: model-independent health checks. Genre-only
  models fail the tie check badly, which is why the original notebook looked random.
"""
from __future__ import annotations

import re
from collections import defaultdict

import numpy as np
import pandas as pd

from .models import FeatureStore, Recommender

_SPLIT = re.compile(r"\s*:\s*|\s+[-\u2013\u2014]\s+|\s*\(|\s+season\s|\s+part\s|\s+vol(?:ume)?\.?\s")
_TRAIL = re.compile(r"(?:[\s\d]+|\s+(?:ii|iii|iv|v|vi|vii|viii|ix|x))$")
_GENERIC = {"the", "a", "an", "love", "life", "home", "dark", "game", "night", "family", "my", "i", "us",
            "special", "seven", "shiva"}


def franchise_key(title: str) -> str | None:
    t = _SPLIT.split(title.lower().strip())[0]
    t = re.sub(r"[^a-z0-9 ]", "", t).strip()
    t = _TRAIL.sub("", t).strip()
    if len(t) < 5 or t in _GENERIC:
        return None
    return t


def franchise_groups(df: pd.DataFrame) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for i, t in enumerate(df["Title"]):
        k = franchise_key(t)
        if k:
            groups[k].append(i)
    # a group is only usable if it contains at least two distinct titles
    return {k: v for k, v in groups.items()
            if len({df.at[i, "Title"].lower() for i in v}) >= 2}


def _top(model: Recommender, rows: np.ndarray, k: int, diversity: float, pool: int):
    s = model.score_chunk(rows)
    tops, boundary = [], []
    for r in range(len(rows)):
        ids, sc = model.rank(s[r], k + 1, diversity=0.0)
        boundary.append(sc[k - 1] == sc[k] if len(sc) > k else False)
        if diversity > 0:
            ids, _ = model.rank(s[r], k, diversity=diversity, pool=pool)
        tops.append(ids[:k])
    return tops, boundary, s


def _franchise_tie_bounds(scores: np.ndarray, relevant: set[int], k: int) -> dict[str, float]:
    """Return best/worst franchise metrics across equal-score orderings at the cutoff."""
    finite = np.flatnonzero(np.isfinite(scores))
    count = min(k, len(finite))
    if count == 0 or not relevant:
        return {
            "hit_best": 0.0, "hit_worst": 0.0,
            "recall_best": 0.0, "recall_worst": 0.0,
            "mrr_best": 0.0, "mrr_worst": 0.0,
        }

    cutoff = np.partition(scores[finite], len(finite) - count)[len(finite) - count]
    above = finite[scores[finite] > cutoff]
    boundary = finite[scores[finite] == cutoff]
    slots = count - len(above)
    relevant_above = [
        i for i in relevant if 0 <= i < len(scores) and np.isfinite(scores[i]) and scores[i] > cutoff
    ]
    relevant_boundary = [
        i for i in relevant if 0 <= i < len(scores) and np.isfinite(scores[i]) and scores[i] == cutoff
    ]
    min_boundary_relevant = max(0, slots - (len(boundary) - len(relevant_boundary)))
    max_boundary_relevant = min(slots, len(relevant_boundary))
    denominator = len(relevant)

    hit_best = bool(relevant_above or max_boundary_relevant)
    hit_worst = bool(relevant_above or min_boundary_relevant)
    recall_best = (len(relevant_above) + max_boundary_relevant) / denominator
    recall_worst = (len(relevant_above) + min_boundary_relevant) / denominator

    if relevant_above:
        first_relevant_score = max(scores[i] for i in relevant_above)
        tied_group_size = int(np.count_nonzero(scores[finite] == first_relevant_score))
        tied_relevant = sum(scores[i] == first_relevant_score for i in relevant_above)
        first_rank = int(np.count_nonzero(scores[finite] > first_relevant_score)) + 1
        mrr_best = 1 / first_rank
        mrr_worst = 1 / (first_rank + tied_group_size - tied_relevant)
    elif max_boundary_relevant:
        mrr_best = 1 / (len(above) + 1)
        mrr_worst = (
            1 / (len(above) + slots - min_boundary_relevant + 1)
            if min_boundary_relevant
            else 0.0
        )
    else:
        mrr_best = mrr_worst = 0.0

    return {
        "hit_best": float(hit_best),
        "hit_worst": float(hit_worst),
        "recall_best": float(recall_best),
        "recall_worst": float(recall_worst),
        "mrr_best": float(mrr_best),
        "mrr_worst": float(mrr_worst),
    }


def split_groups(groups: dict[str, list[int]]) -> tuple[dict, dict]:
    """Deterministic 50/50 split of franchise groups into (tune, test) so weights tuned on
    one half are reported on the other half."""
    keys = sorted(groups)
    return ({k: groups[k] for k in keys[0::2]}, {k: groups[k] for k in keys[1::2]})


def evaluate(model: Recommender, k: int = 10, diversity: float = 0.0, chunk: int = 400,
             pool: int = 50, groups: dict[str, list[int]] | None = None) -> dict:
    store = model.store
    df = store.df
    n = len(df)
    groups = groups if groups is not None else franchise_groups(df)
    rel: dict[int, set[int]] = {}
    for members in groups.values():
        for i in members:
            others = {j for j in members if df.at[j, "Title"].lower() != df.at[i, "Title"].lower()}
            if others:
                rel[i] = others
    fr_queries = np.array(sorted(rel))

    genre_sets = store._genre_sets
    types = df["Content Type"].to_numpy()
    hits, recalls, rrs = [], [], []
    jacc, div, same_type, ties = [], [], [], []
    metric_bounds = {name: [] for name in ("hit_best", "hit_worst", "recall_best",
                                           "recall_worst", "mrr_best", "mrr_worst")}
    seen = np.zeros(n, dtype=bool)

    for start in range(0, n, chunk):
        rows = np.arange(start, min(start + chunk, n))
        tops, boundary, score_rows = _top(model, rows, k, diversity, pool)
        ties.extend(boundary)
        for q, ids in zip(rows, tops):
            seen[ids] = True
            gq = genre_sets[q]
            jac = [len(gq & genre_sets[j]) / len(gq | genre_sets[j]) for j in ids]
            jacc.append(np.mean(jac))
            same_type.append(np.mean(types[ids] == types[q]))
            pair = [1 - len(genre_sets[a] & genre_sets[b]) / len(genre_sets[a] | genre_sets[b])
                    for ai, a in enumerate(ids) for b in ids[ai + 1:]]
            div.append(np.mean(pair) if pair else 0.0)
            if q in rel:
                ranked_rel = [j in rel[q] for j in ids]
                hits.append(any(ranked_rel))
                recalls.append(sum(ranked_rel) / len(rel[q]))
                first = next((r for r, ok in enumerate(ranked_rel, 1) if ok), None)
                rrs.append(1 / first if first else 0.0)
                if diversity == 0:
                    bounds = _franchise_tie_bounds(score_rows[q - start], rel[q], k)
                    for name, value in bounds.items():
                        metric_bounds[name].append(value)

    metrics = {
        "k": k,
        "franchise_queries": int(len(fr_queries)),
        f"franchise_hit@{k}": float(np.mean(hits)),
        f"franchise_recall@{k}": float(np.mean(recalls)),
        f"franchise_mrr@{k}": float(np.mean(rrs)),
        f"genre_jaccard@{k}": float(np.mean(jacc)),
        f"genre_diversity@{k}": float(np.mean(div)),
        f"same_type@{k}": float(np.mean(same_type)),
        "catalog_coverage": float(seen.mean()),
        "boundary_tie_rate": float(np.mean(ties)),
    }
    for metric in ("hit", "recall", "mrr"):
        for bound in ("best", "worst"):
            values = metric_bounds[f"{metric}_{bound}"]
            metrics[f"franchise_{metric}@{k}_tie_{bound}"] = float(np.mean(values)) if values else None
    return metrics


def results_table(results: dict[str, dict]) -> pd.DataFrame:
    return pd.DataFrame(results).T
