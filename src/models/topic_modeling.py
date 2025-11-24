# src/models/topic_modeling.py
"""
Fase 5: Topic Modeling para tuits políticos (Elecciones Colombia 2026)

- Lee data/processed/tweets_features.csv
- Ajusta un modelo LDA sobre 'clean_text' (con stopwords en español eliminadas)
- Extrae palabras clave por tema
- Asigna topic_id a cada tuit
- Guarda:
    - data/processed/tweets_topics.csv
    - data/processed/tweets_features_with_topics.csv
"""

import os
from typing import List, Tuple

import pandas as pd
import numpy as np

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

import nltk
from nltk.corpus import stopwords

# Rutas
FEATURES_CSV = "data/processed/tweets_features.csv"
TOPICS_CSV = "data/processed/tweets_topics.csv"
FEATURES_WITH_TOPICS_CSV = "data/processed/tweets_features_with_topics.csv"

os.makedirs("data/processed", exist_ok=True)

# === STOPWORDS PARA TOPIC MODELING ===
nltk.download("stopwords", quiet=True)
stopwords_es = set(stopwords.words("spanish"))

extra_stops = {
    "rt", "via", "com", "tco", "co", "amp",
    "https", "http", "www",
    "si", "asi", "solo", "aun",
    "mas", "muy", "tan",
    "sr", "sra", "ud", "uds",
    "del", "al",
    "pues", "entonces", "ahi", "aqui", "aca",
    "donde", "cuando", "porque",
    "esto", "esta", "ese", "esa",
    "aquel", "aquella",
    "colombia",      # si quieres luego la quitas
    "youtu", "youtube", "shorts", "be",  # basura de enlaces
}

stopwords_total = stopwords_es.union(extra_stops)


def load_features() -> pd.DataFrame:
    if not os.path.exists(FEATURES_CSV):
        raise FileNotFoundError(f"No se encontró {FEATURES_CSV}. Ejecuta antes build_features.py")
    print(f"Cargando features desde {FEATURES_CSV} ...")
    df = pd.read_csv(FEATURES_CSV)
    return df


def build_lda_model(
    texts: List[str],
    n_topics: int = 8,
    max_features: int = 5000,
    min_df: int = 5,
    max_df: float = 0.7,
    random_state: int = 42
) -> Tuple[LatentDirichletAllocation, CountVectorizer]:
    """
    Ajusta un modelo LDA sobre la lista de textos usando stopwords en español.
    """
    print("Vectorizando textos para LDA (con stopwords en español)...")
    vectorizer = CountVectorizer(
        max_features=max_features,
        min_df=min_df,
        max_df=max_df,
        stop_words=list(stopwords_total),  # <-- AQUÍ EL CAMBIO
        strip_accents="unicode"  # normaliza acentos
)

    dtm = vectorizer.fit_transform(texts)

    print(f"Ajustando LDA con {n_topics} temas...")
    lda = LatentDirichletAllocation(
        n_components=n_topics,
        random_state=random_state,
        learning_method="batch",
        max_iter=20
    )
    lda.fit(dtm)

    return lda, vectorizer


def print_topics(lda: LatentDirichletAllocation, vectorizer: CountVectorizer, n_top_words: int = 10) -> None:
    feature_names = vectorizer.get_feature_names_out()
    for topic_idx, topic in enumerate(lda.components_):
        top_indices = topic.argsort()[::-1][:n_top_words]
        top_words = [feature_names[i] for i in top_indices]
        print(f"Tema {topic_idx}: {', '.join(top_words)}")


def assign_topics(lda: LatentDirichletAllocation, vectorizer: CountVectorizer, texts: List[str]) -> np.ndarray:
    dtm = vectorizer.transform(texts)
    topic_distrib = lda.transform(dtm)  # shape: (n_docs, n_topics)
    topic_ids = topic_distrib.argmax(axis=1)
    return topic_ids


def main() -> None:
    print("Fase 5: Topic Modeling (LDA)")

    # 1) Cargar datos
    df = load_features()

    # 2) Filtrar textos no vacíos
    texts = df["clean_text"].astype(str).tolist()

    # 3) Entrenar LDA
    lda, vectorizer = build_lda_model(
        texts=texts,
        n_topics=8,       # puedes ajustar
        max_features=5000,
        min_df=5,
        max_df=0.7
    )

    print("\nPalabras clave por tema (stopwords filtradas):")
    print_topics(lda, vectorizer, n_top_words=12)

    # 4) Asignar topic_id a cada tuit
    topic_ids = assign_topics(lda, vectorizer, texts)
    df_topics = pd.DataFrame({
        "id": df["id"],
        "topic_id": topic_ids
    })

    # 5) Guardar solo topics
    df_topics.to_csv(TOPICS_CSV, index=False, encoding="utf-8")
    print(f"Topics por tuit guardados en {TOPICS_CSV}")

    # 6) Unir al dataframe de features y guardar
    df_with_topics = df.copy()
    df_with_topics["topic_id"] = topic_ids
    df_with_topics.to_csv(FEATURES_WITH_TOPICS_CSV, index=False, encoding="utf-8")
    print(f"Features + topics guardados en {FEATURES_WITH_TOPICS_CSV}")

    print("Fase 5 completada.")


if __name__ == "__main__":
    main()
