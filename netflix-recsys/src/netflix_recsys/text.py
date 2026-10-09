"""Text cleaning utilities.

Differences from the original notebook version:
* regexes are raw strings and precompiled
* apostrophes are *removed* ("frank's" -> "franks") but other punctuation becomes a
  space ("well-known" -> "well known") so words are not glued together
* stopwords come from scikit-learn, so no runtime ``nltk.download`` is needed
* stemming is optional and cached
"""
from __future__ import annotations

import re
from functools import lru_cache

from nltk.stem import SnowballStemmer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

_stemmer = SnowballStemmer("english")

_BRACKET = re.compile(r"\[.*?\]")
_URL = re.compile(r"https?://\S+|www\.\S+")
_HTML = re.compile(r"<.*?>+")
_APOSTROPHE = re.compile(r"['\u2019]")
_NON_WORD = re.compile(r"[^\w\s]|_")
_DIGIT_WORD = re.compile(r"\w*\d\w*")

STOPWORDS = frozenset(ENGLISH_STOP_WORDS)


@lru_cache(maxsize=100_000)
def _stem(word: str) -> str:
    return _stemmer.stem(word)


def clean(text: object, stem: bool = True) -> str:
    """Normalise free text for TF-IDF. Missing values give an empty string."""
    if text is None or (isinstance(text, float) and text != text):
        return ""
    t = str(text).lower()
    t = _BRACKET.sub(" ", t)
    t = _URL.sub(" ", t)
    t = _HTML.sub(" ", t)
    t = _APOSTROPHE.sub("", t)
    t = _NON_WORD.sub(" ", t)
    t = _DIGIT_WORD.sub(" ", t)
    words = [w for w in t.split() if w not in STOPWORDS and len(w) > 1]
    if stem:
        words = [_stem(w) for w in words]
    return " ".join(words)


def split_list(value: str) -> list[str]:
    """Tokenise a comma separated field ("Dramas, TV Comedies") into lowercase items."""
    return [p.strip().lower() for p in str(value).split(",") if p.strip()]
