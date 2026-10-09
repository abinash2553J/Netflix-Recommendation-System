"""Run the offline evaluation and write results/metrics.{json,md}.

    python scripts/run_eval.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from netflix_recsys import FeatureStore, load_catalog
from netflix_recsys.evaluate import evaluate, franchise_groups, results_table
from netflix_recsys.models import MODEL_WEIGHTS

OUT = Path(__file__).resolve().parents[1] / "results"
K = 10


def main() -> None:
    OUT.mkdir(exist_ok=True)
    df = load_catalog()
    store = FeatureStore(df, stem=True)
    print(f"{len(df)} titles, {len(franchise_groups(df))} franchise groups")

    main_rows = {}
    for name in ["genre", "description", "lsa", "hybrid"]:
        t = time.time()
        main_rows[name] = evaluate(store.model(name), k=K)
        print(f"{name:12s} {time.time() - t:5.1f}s", {k: round(v, 3) for k, v in main_rows[name].items() if "hit" in k})
    main_rows["hybrid + MMR(0.3)"] = evaluate(store.model("hybrid"), k=K, diversity=0.3)
    main_rows["hybrid + MMR(0.5)"] = evaluate(store.model("hybrid"), k=K, diversity=0.5)

    # Ablation 1: stemming on/off for the description features
    nostem = FeatureStore(df, stem=False)
    ablation = {
        "hybrid (stemmed)": main_rows["hybrid"],
        "hybrid (no stemming)": evaluate(nostem.model("hybrid"), k=K),
    }
    # Ablation 2: drop one block at a time from the hybrid
    base = MODEL_WEIGHTS["hybrid"]
    for block in base:
        w = {b: v for b, v in base.items() if b != block}
        ablation[f"hybrid - {block}"] = evaluate(store.model(weights=w, name=f"no_{block}"), k=K)

    (OUT / "metrics.json").write_text(json.dumps({"main": main_rows, "ablation": ablation}, indent=2))
    fmt = lambda d: results_table(d).round(3).fillna("N/A").to_markdown()
    (OUT / "metrics.md").write_text(
        f"## Model comparison (k={K})\n\n"
        "Franchise point metrics use deterministic title ordering for equal scores. "
        "For non-MMR rows, `_tie_best` and `_tie_worst` show bounds over equal-score orderings; "
        "these bounds are not applicable to MMR reranking.\n\n"
        f"{fmt(main_rows)}\n\n## Ablations\n\n{fmt(ablation)}\n")
    print((OUT / "metrics.md").read_text())


if __name__ == "__main__":
    main()
