from netflix_recsys.text import clean, split_list


def test_raw_string_regexes_do_not_warn_and_strip_noise():
    out = clean("Visit https://x.com or www.y.org [ad] <b>Great</b> film 2020 abc123", stem=False)
    assert out == "visit great film"


def test_apostrophes_removed_but_hyphens_split():
    assert clean("Anne Frank's long-lost diary", stem=False) == "anne franks long lost diary"


def test_stopwords_filtered_and_stemming_optional():
    assert clean("the running dogs", stem=False) == "running dogs"
    assert clean("the running dogs", stem=True) == "run dog"


def test_missing_values_become_empty_not_nan_token():
    assert clean(float("nan")) == ""
    assert clean(None) == ""


def test_split_list():
    assert split_list("Dramas,  TV Comedies ,") == ["dramas", "tv comedies"]
