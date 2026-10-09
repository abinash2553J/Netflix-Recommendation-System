from fastapi.testclient import TestClient

from netflix_recsys import api


def make_client(tiny_df, tmp_path, monkeypatch):
    path = tmp_path / "tiny.csv"
    tiny_df.drop(columns=["Year", "Imdb"]).to_csv(path, index=False)
    monkeypatch.setenv("NETFLIX_DATA", str(path))
    return TestClient(api.app)


def test_endpoints(tiny_df, tmp_path, monkeypatch):
    with make_client(tiny_df, tmp_path, monkeypatch) as c:
        assert c.get("/health").json()["status"] == "ok"
        assert "Cake Wars" in c.get("/titles", params={"q": "cake war"}).json()["results"]

        r = c.get("/recommend", params={"title": "Space Quest", "k": 2})
        assert r.status_code == 200
        body = r.json()
        assert body["results"][0]["title"] == "Space Quest 2"
        assert "why" in body["results"][0]

        miss = c.get("/recommend", params={"title": "Space Quet"})
        assert miss.status_code == 404
        assert "Space Quest" in miss.json()["detail"]["suggestions"]

        assert c.get("/recommend", params={"title": "Space Quest", "k": 0}).status_code == 422
