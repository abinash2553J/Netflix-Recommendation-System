import numpy as np
import pytest
from sklearn.metrics.pairwise import cosine_similarity

from netflix_recsys import TitleNotFound


def test_query_never_in_own_results_and_duplicates_excluded(tiny_store):
    titles = [r.title for r in tiny_store.model("hybrid").recommend("Courtroom Drama", k=7)]
    assert "Courtroom Drama" not in titles


def test_franchise_sequel_ranks_first(tiny_store):
    recs = tiny_store.model("hybrid").recommend("Space Quest", k=3)
    assert recs[0].title == "Space Quest 2"


def test_scores_sorted_descending(tiny_store):
    scores = [r.score for r in tiny_store.model("hybrid").recommend("Cake Wars", k=5)]
    assert scores == sorted(scores, reverse=True)


def test_rank_uses_title_order_to_resolve_equal_scores_at_cutoff(tiny_store):
    model = tiny_store.model("hybrid")
    scores = np.ones(len(tiny_store.df))
    scores[[5, 6]] = -np.inf

    ids, _ = model.rank(scores, k=3)

    actual = tiny_store.df.iloc[ids]["Title"].tolist()
    expected = sorted(
        tiny_store.df.loc[np.isfinite(scores), "Title"].unique(),
        key=str.casefold,
    )[:3]
    assert actual == expected


def test_hybrid_equals_weighted_sum_of_block_cosines(tiny_store):
    w = {"genre": 0.5, "desc": 0.3, "cast": 0.2}
    model = tiny_store.model(weights=w, name="t")
    got = model.X @ model.X[0].T
    got = got.toarray().ravel()
    want = sum(w[b] * cosine_similarity(tiny_store.blocks[b], tiny_store.blocks[b][0]).ravel() for b in w)
    np.testing.assert_allclose(got, want, atol=1e-9)


def test_unknown_title_gives_suggestions(tiny_store):
    with pytest.raises(TitleNotFound) as e:
        tiny_store.model().recommend("Space Quet")
    assert "Space Quest" in e.value.suggestions


def test_lookup_is_case_insensitive(tiny_store):
    assert tiny_store.resolve("cake WARS") == tiny_store.resolve("Cake Wars")


def test_content_type_filter(tiny_store):
    recs = tiny_store.model("hybrid").recommend("Bake Off Kids", k=5, content_type="Movie")
    assert recs and all(r.content_type == "Movie" for r in recs)


def test_mmr_returns_k_distinct_items(tiny_store):
    recs = tiny_store.model("hybrid").recommend("Space Quest", k=4, diversity=0.5)
    titles = [r.title for r in recs]
    assert len(titles) == len(set(titles)) == 4


def test_explanation_contains_shared_signals(tiny_store):
    top = tiny_store.model("hybrid").recommend("Space Quest", k=1)[0]
    assert "Ann Lee" in top.why["shared_cast"]
    assert "action & adventure" in top.why["shared_genres"]
