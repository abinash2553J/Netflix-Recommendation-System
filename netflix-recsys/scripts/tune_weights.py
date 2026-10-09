"""Small grid search over hybrid block weights.

Weights are tuned on one half of the franchise groups and reported on the other half, with a
hard constraint on the tie rate (a model that cannot rank is not acceptable no matter what
its hit rate is). The grid is deliberately small: the franchise signal is a proxy, and a
large search would just overfit it.

    python scripts/tune_weights.py
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

from netflix_recsys import FeatureStore, load_catalog
from netflix_recsys.evaluate import evaluate, franchise_groups, split_groups

OUT = Path(__file__).resolve().parents[1] / "results"


def main() -> None:
    df = load_catalog()
    store = FeatureStore(df)
    tune, test = split_groups(franchise_groups(df))
    rows = []
    for desc, lsa, cast, director in itertools.product([0.35, 0.45], [0.05, 0.10, 0.20], [0.10, 0.20], [0.05]):
        w = {"genre": 0.25, "desc": desc, "lsa": lsa, "cast": cast, "director": director}
        m = evaluate(store.model(weights=w, name="grid"), groups=tune)
        rows.append({"weights": w, "tune_mrr": m["franchise_mrr@10"], "tune_hit": m["franchise_hit@10"],
                     "ties": m["boundary_tie_rate"]})
        print(w, round(m["franchise_mrr@10"], 3), round(m["franchise_hit@10"], 3), round(m["boundary_tie_rate"], 3))
    ok = [r for r in rows if r["ties"] < 0.01]
    best = max(ok, key=lambda r: r["tune_mrr"])
    default_w = {"genre": 0.25, "desc": 0.35, "lsa": 0.25, "cast": 0.10, "director": 0.05}  # initial hand-picked weights
    report = {
        "best_weights": best["weights"],
        "held_out_best": evaluate(store.model(weights=best["weights"]), groups=test),
        "held_out_default": evaluate(store.model(weights=default_w), groups=test),
        "grid": rows,
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "tuning.json").write_text(json.dumps(report, indent=2))
    for key in ("held_out_default", "held_out_best"):
        r = report[key]
        print(key, {k: round(v, 3) for k, v in r.items() if k.startswith("franchise") or k == "boundary_tie_rate"})
    print("best", best["weights"])


if __name__ == "__main__":
    main()
