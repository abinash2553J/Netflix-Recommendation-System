from itertools import permutations, product

import numpy as np

from netflix_recsys.evaluate import _franchise_tie_bounds, evaluate, franchise_groups, franchise_key


def test_franchise_key_strips_subtitles_and_numbers():
    assert franchise_key("Narcos: Mexico") == "narcos"
    assert franchise_key("My Stupid Boss 2") == "my stupid boss"
    assert franchise_key("The") is None


def test_groups_need_two_distinct_titles(tiny_df):
    groups = franchise_groups(tiny_df)
    assert any(len(v) >= 2 for v in groups.values())
    assert "courtroom drama" not in groups  # same title twice is not a franchise


def test_evaluate_returns_valid_ranges(tiny_store):
    m = evaluate(tiny_store.model("hybrid"), k=3, chunk=4)
    for key in ["franchise_hit@3", "franchise_mrr@3", "catalog_coverage", "same_type@3"]:
        assert 0.0 <= m[key] <= 1.0
    for metric in ("hit", "recall", "mrr"):
        point = m[f"franchise_{metric}@3"]
        assert m[f"franchise_{metric}@3_tie_worst"] <= point
        assert point <= m[f"franchise_{metric}@3_tie_best"]


def test_tie_bounds_cover_all_boundary_orders():
    scores = np.array([0.9, 0.5, 0.5, 0.5, 0.1])

    bounds = _franchise_tie_bounds(scores, relevant={2}, k=2)

    assert bounds == {
        "hit_best": 1.0,
        "hit_worst": 0.0,
        "recall_best": 1.0,
        "recall_worst": 0.0,
        "mrr_best": 0.5,
        "mrr_worst": 0.0,
    }


def test_tie_bounds_include_fully_ranked_ties_and_earlier_relevance():
    scores = np.array([0.9, 0.9, 0.1])

    bounds = _franchise_tie_bounds(scores, relevant={1}, k=2)

    assert bounds == {
        "hit_best": 1.0,
        "hit_worst": 1.0,
        "recall_best": 1.0,
        "recall_worst": 1.0,
        "mrr_best": 1.0,
        "mrr_worst": 0.5,
    }


def test_tie_bounds_account_for_relevant_items_above_cutoff():
    scores = np.array([0.9, 0.8, 0.8, 0.1])

    bounds = _franchise_tie_bounds(scores, relevant={0, 2}, k=2)

    assert bounds == {
        "hit_best": 1.0,
        "hit_worst": 1.0,
        "recall_best": 1.0,
        "recall_worst": 0.5,
        "mrr_best": 1.0,
        "mrr_worst": 1.0,
    }


def test_tie_bounds_match_exhaustive_orderings():
    scores = np.array([0.9, 0.9, 0.5, 0.5, 0.5, 0.1])
    relevant = {1, 3, 5}
    groups = ([0, 1], [2, 3, 4], [5])
    outcomes = []

    for tied_orders in product(*(permutations(group) for group in groups)):
        ranking = [item for group in tied_orders for item in group]
        top = ranking[:4]
        relevant_ranks = [rank for rank, item in enumerate(top, 1) if item in relevant]
        outcomes.append((
            float(bool(relevant_ranks)),
            len(relevant_ranks) / len(relevant),
            1 / relevant_ranks[0] if relevant_ranks else 0.0,
        ))

    bounds = _franchise_tie_bounds(scores, relevant=relevant, k=4)

    assert bounds["hit_worst"] == min(outcome[0] for outcome in outcomes)
    assert bounds["hit_best"] == max(outcome[0] for outcome in outcomes)
    assert bounds["recall_worst"] == min(outcome[1] for outcome in outcomes)
    assert bounds["recall_best"] == max(outcome[1] for outcome in outcomes)
    assert bounds["mrr_worst"] == min(outcome[2] for outcome in outcomes)
    assert bounds["mrr_best"] == max(outcome[2] for outcome in outcomes)


def test_mmr_evaluation_marks_similarity_tie_bounds_not_applicable(tiny_store):
    metrics = evaluate(tiny_store.model("hybrid"), k=3, diversity=0.3, chunk=4)

    for metric in ("hit", "recall", "mrr"):
        assert metrics[f"franchise_{metric}@3_tie_best"] is None
        assert metrics[f"franchise_{metric}@3_tie_worst"] is None
