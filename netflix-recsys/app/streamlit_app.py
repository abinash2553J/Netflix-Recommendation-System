"""Demo UI.   streamlit run app/streamlit_app.py"""
import streamlit as st

from netflix_recsys import FeatureStore, MODEL_WEIGHTS, load_catalog

st.set_page_config(page_title="Netflix recommender", page_icon="🎬", layout="wide")


@st.cache_resource(show_spinner="Building feature matrices...")
def get_models():
    store = FeatureStore(load_catalog())
    return store, {n: store.model(n) for n in MODEL_WEIGHTS}


store, models = get_models()

st.title("🎬 Netflix content-based recommender")
st.caption("Hybrid of genre, description (TF-IDF + LSA), cast and director similarity, "
           "with optional MMR re-ranking and per-result explanations.")

with st.sidebar:
    st.header("Settings")
    model_name = st.radio("Model", list(MODEL_WEIGHTS), index=list(MODEL_WEIGHTS).index("hybrid"),
                          help="'genre' is the original notebook baseline.")
    k = st.slider("Results", 3, 20, 10)
    diversity = st.slider("Diversity (MMR)", 0.0, 0.8, 0.0, 0.1,
                          help="Higher values trade a little relevance for more varied results.")
    ctype = st.selectbox("Content type", ["Any", "Movie", "TV Show"])

query = st.text_input("Type a title", placeholder="e.g. Narcos, Stranger Things, Bleach")
if query:
    options = store.search(query, 10)
    exact = [t for t in options if t.lower() == query.lower().strip()]
    choice = st.selectbox("Pick the title", options, index=options.index(exact[0]) if exact else 0)
    recs = models[model_name].recommend(
        choice, k=k, diversity=diversity, content_type=None if ctype == "Any" else ctype)
    src = store.df.iloc[store.resolve(choice)]
    st.subheader(f"Because you watched: {src['Title']}")
    st.write(f"*{src['Content Type']} · {src['Genres']}*")
    st.write(src["Description"])
    st.divider()
    for r in recs:
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            meta = " · ".join(str(x) for x in [r.content_type, r.year, f"IMDb {r.imdb}" if r.imdb else None] if x)
            c1.markdown(f"**{r.title}**  \n{meta}  \n_{r.genres}_")
            c2.metric("Similarity", f"{r.score:.2f}")
            st.write(r.description)
            bits = []
            if r.why.get("shared_genres"): bits.append("genres: " + ", ".join(r.why["shared_genres"]))
            if r.why.get("shared_cast"): bits.append("cast: " + ", ".join(r.why["shared_cast"]))
            if r.why.get("shared_terms"): bits.append("plot terms: " + ", ".join(r.why["shared_terms"]))
            if bits:
                st.caption("Why: " + " | ".join(bits))
else:
    st.info("Search for a title to get recommendations.")
