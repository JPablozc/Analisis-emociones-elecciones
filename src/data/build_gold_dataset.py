# src/data/build_gold_dataset.py
"""
Fase 6: Construcción del dataset GOLD para análisis y dashboard.

Toma como entrada:
- data/processed/tweets_features_with_topics.csv (idealmente)
- o data/processed/tweets_features.csv si no existen topics.

Genera:
- data/processed/tweets_gold.csv   -> dataset fila a fila con columnas clave
- data/processed/candidate_daily_metrics.csv -> métricas agregadas por candidato y día

Opcionalmente también escribe tabla 'tweets_gold' en la base SQLite.
"""

import os
import sqlite3
from typing import List

import pandas as pd

RAW_DB = "data/raw/twitter_data.db"
FEATURES_WITH_TOPICS_CSV = "data/processed/tweets_features_with_topics.csv"
FEATURES_CSV = "data/processed/tweets_features.csv"
GOLD_CSV = "data/processed/tweets_gold.csv"
AGG_CSV = "data/processed/candidate_daily_metrics.csv"

os.makedirs("data/processed", exist_ok=True)


def load_features_with_topics() -> pd.DataFrame:
    """Carga features con topics, o sin topics si no existen."""
    if os.path.exists(FEATURES_WITH_TOPICS_CSV):
        print(f"Cargando features + topics desde {FEATURES_WITH_TOPICS_CSV}")
        df = pd.read_csv(FEATURES_WITH_TOPICS_CSV)
    elif os.path.exists(FEATURES_CSV):
        print(f"No se encontró {FEATURES_WITH_TOPICS_CSV}, usando {FEATURES_CSV} (sin topics).")
        df = pd.read_csv(FEATURES_CSV)
    else:
        raise FileNotFoundError(
            f"No se encontraron ni {FEATURES_WITH_TOPICS_CSV} ni {FEATURES_CSV}. "
            "Ejecuta antes src.features.build_features y src.models.topic_modeling."
        )

    return df


def ensure_basic_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Asegura columnas derivadas básicas como 'date' y 'sentiment_score'."""
    # created_at -> datetime + date
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["date"] = df["created_at"].dt.date
    else:
        print("No existe 'created_at' en el dataframe. 'date' no se podrá generar.")
        df["date"] = pd.NaT

    # sentiment_score = POS - NEG
    if "sentiment_pos" in df.columns and "sentiment_neg" in df.columns:
        df["sentiment_score"] = df["sentiment_pos"] - df["sentiment_neg"]
    else:
        print("No se encontraron columnas sentiment_pos/sentiment_neg. "
              "No se generará 'sentiment_score'.")
        df["sentiment_score"] = None

    return df


def select_gold_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Selecciona y ordena las columnas clave para el dataset GOLD."""
    # Lista deseada de columnas (solo se incluirán las que existan)
    desired_cols: List[str] = [
        "id",
        "created_at",
        "date",
        "candidate",
        "source",
        "text",
        "clean_text",
        "tokens",
        "n_tokens",
        "n_chars",
        "n_mentions",
        "n_hashtags",
        "sentiment_label",
        "sentiment_pos",
        "sentiment_neu",
        "sentiment_neg",
        "sentiment_score",
        "emotion_label",
        "emotion_joy",
        "emotion_anger",
        "emotion_sadness",
        "emotion_fear",
        "topic_id",
        "categoria",   # por si la tenías en la BD original
        "lang",        # idem
    ]

    existing_cols = [c for c in desired_cols if c in df.columns]

    gold_df = df[existing_cols].copy()
    print(f"Dataset GOLD tendrá {len(existing_cols)} columnas y {len(gold_df)} filas.")
    return gold_df


def build_candidate_daily_metrics(gold_df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye métricas agregadas por candidato y día:
    - n_tweets
    - sentiment_score medio
    - % positivos / negativos / neutros
    """
    print("Calculando métricas agregadas por candidato y día...")

    # Asegurar que candidate y date existan
    if "candidate" not in gold_df.columns or "date" not in gold_df.columns:
        print("gold_df no tiene 'candidate' o 'date'. "
              "No se pueden construir métricas diarias.")
        return pd.DataFrame()

    # Conteo total de tuits
    grp = gold_df.groupby(["candidate", "date"])

    agg = grp.agg(
        n_tweets=("id", "count"),
        mean_sentiment=("sentiment_score", "mean")
    ).reset_index()

    # Conteo por etiqueta de sentimiento
    if "sentiment_label" in gold_df.columns:
        sentiment_counts = (
            gold_df
            .pivot_table(
                index=["candidate", "date"],
                columns="sentiment_label",
                values="id",
                aggfunc="count",
                fill_value=0
            )
            .reset_index()
        )
        sentiment_counts.columns.name = None

        # Unir
        agg = agg.merge(sentiment_counts, on=["candidate", "date"], how="left")

        # Sacar porcentajes si hay columnas POS/NEG/NEU
        for col in ["POS", "NEG", "NEU"]:
            if col in agg.columns:
                agg[f"pct_{col.lower()}"] = agg[col] / agg["n_tweets"]
    else:
        print("'sentiment_label' no está en GOLD. No se agregan columnas POS/NEG/NEU.")

    print(f"Métricas diarias: {len(agg)} filas.")
    return agg


def save_to_sqlite(df_gold: pd.DataFrame, df_agg: pd.DataFrame) -> None:
    """Guarda tablas en SQLite (opcional)."""
    if not os.path.exists(RAW_DB):
        print(f"No se encontró la base de datos {RAW_DB}. No se guardarán tablas SQL.")
        return

    with sqlite3.connect(RAW_DB) as conn:
        df_gold.to_sql("tweets_gold", conn, if_exists="replace", index=False)
        print("Tabla 'tweets_gold' guardada en SQLite.")

        if not df_agg.empty:
            df_agg.to_sql("candidate_daily_metrics", conn, if_exists="replace", index=False)
            print("Tabla 'candidate_daily_metrics' guardada en SQLite.")


def main() -> None:
    print("Fase 6: Construcción del dataset GOLD")

    # 1. Cargar features (con topics si existen)
    df = load_features_with_topics()

    # 2. Asegurar columnas derivadas
    df = ensure_basic_columns(df)

    # 3. Seleccionar columnas clave
    gold_df = select_gold_columns(df)

    # 4. Guardar GOLD row-level
    gold_df.to_csv(GOLD_CSV, index=False, encoding="utf-8")
    print(f"Dataset GOLD guardado en {GOLD_CSV}")

    # 5. Construir y guardar métricas agregadas por candidato y día
    agg_df = build_candidate_daily_metrics(gold_df)
    if not agg_df.empty:
        agg_df.to_csv(AGG_CSV, index=False, encoding="utf-8")
        print(f"Métricas diarias guardadas en {AGG_CSV}")

    # 6. Guardar también en SQLite
    save_to_sqlite(gold_df, agg_df)

    print("Fase 6 completada.")


if __name__ == "__main__":
    main()
