import pandas as pd
import pytest

from netflix_recsys import FeatureStore


@pytest.fixture(scope="session")
def tiny_df():
    rows = [
        ("Space Quest", "A crew of astronauts battles aliens on a distant planet.", "Sci-Fi Movies, Action & Adventure", "Ann Lee, Bo Chan", "Dee Kay", "Movie"),
        ("Space Quest 2", "The astronauts return to fight a new alien threat in deep space.", "Sci-Fi Movies, Action & Adventure", "Ann Lee, Bo Chan", "Dee Kay", "Movie"),
        ("Galaxy Raiders", "Pirates raid starships among alien worlds and distant planets.", "Sci-Fi Movies, Action & Adventure", "Cy Dunn", "Eve Ray", "Movie"),
        ("Bake Off Kids", "Children compete to bake the tastiest cakes and pastries.", "Reality TV", "Gus Fox", "", "TV Show"),
        ("Cake Wars", "Bakers compete to make elaborate cakes in a tense contest.", "Reality TV", "Gus Fox", "", "TV Show"),
        ("Courtroom Drama", "A lawyer defends an innocent man accused of murder.", "Dramas", "Hal Poe", "Ivy Lu", "Movie"),
        ("Courtroom Drama", "Duplicate title with a different plot about a judge.", "Dramas", "Hal Poe", "Ivy Lu", "TV Show"),
        ("Laugh Out", "A comedian tells jokes about airports and family dinners.", "Stand-Up Comedy", "Jo Kim", "", "Movie"),
    ]
    return pd.DataFrame(rows, columns=["Title", "Description", "Genres", "Cast", "Director", "Content Type"]).assign(
        **{"Release Date": 2020.0, "Imdb Score": "7.0/10"}).pipe(_derive)


def _derive(df):
    df["Year"] = df["Release Date"].astype("Int64")
    df["Imdb"] = 7.0
    return df


@pytest.fixture(scope="session")
def tiny_store(tiny_df):
    return FeatureStore(tiny_df, lsa_dims=3)
