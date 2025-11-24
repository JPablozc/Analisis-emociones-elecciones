# src/features/build_features.py
"""
Fase 3: Feature Engineering para tuits políticos (Elecciones Colombia 2026)

Lee tweets limpios desde CSV / SQLite, genera:
- tokens limpios (tokenize_pro)
- features numéricos (longitud, nº tokens, menciones, hashtags)
- mapeo de hashtag -> candidato
- (opcional) features de sentimiento con pysentimiento

Guarda el resultado en:
- data/processed/tweets_features.csv
- tabla 'tweets_features' en data/raw/twitter_data.db
"""

import os
import re
import unicodedata
import sqlite3
from typing import List, Dict, Any, Optional

import pandas as pd

# === RUTAS BASE ===
RAW_DB = "data/raw/twitter_data.db"
CLEAN_CSV = "data/processed/tweets_clean.csv"
FEATURES_CSV = "data/processed/tweets_features.csv"

os.makedirs("data/processed", exist_ok=True)

# === STOPWORDS Y TOKENIZACIÓN ===
import nltk
from nltk.corpus import stopwords

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
    "colombia",  
}

stopwords_total = stopwords_es.union(extra_stops)


def tokenize_pro(text: str) -> List[str]:
    """Tokenizador para análisis político en español."""
    if not isinstance(text, str):
        return []

    # Normalizar acentos
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    # Minúsculas
    text = text.lower()
    # Quitar URLs
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    # Quitar menciones
    text = re.sub(r"@\w+", " ", text)
    # Quitar # pero dejar palabra
    text = text.replace("#", " ")
    # Dejar solo letras
    text = re.sub(r"[^a-zñáéíóúü ]", " ", text)
    # Tokenizar
    tokens = text.split()
    # Filtrar stopwords, cortas, numéricas
    tokens = [
        t for t in tokens
        if t not in stopwords_total
        and len(t) > 3
        and not t.isnumeric()
    ]
    return tokens


# === MAPEO HASHTAG -> CANDIDATO ===

CANDIDATE_SOURCES: Dict[str, List[str]] = {
    "Ivan Cepeda": ["#IvanCepeda", "#CepedaPresidente", "#Cepeda"],
    "Luis Gilberto Murillo": ["#LuisGilbertoMurillo", "#MurilloPresidente", "#Murillo2026"],
    "Maria Fernanda Cabal": ["#MariaFernandaCabal", "#CabalPresidenta", "#Cabal", "#Cabal2026"],
    "Claudia Lopez": ["#ClaudiaLopez", "#LopezPresidenta", "#ClaudiaLopez2026"],
    "Gustavo Bolivar": ["#GustavoBolivar", "#BolivarPresidente", "#Bolivar2026"],
    "Andres Guerra": ["#AndresGuerra", "#AndresGuerra2026"],
    "Gustavo Petro": ["#Petro", "#GustavoPetro", "#PetroColombia"],
    "Polo Polo": ["#PoloPolo", "#MiguelPoloPolo", "#PoloPoloColombia"],
    # puedes añadir más mapeos si quieres
}


def source_to_candidate(source: str) -> str:
    """Mapea el hashtag de 'source' a un nombre de candidato."""
    if not isinstance(source, str):
        return "Otro"

    src_lower = source.lower()
    for cand, tags in CANDIDATE_SOURCES.items():
        for tag in tags:
            if src_lower == tag.lower():
                return cand
    return "Otro"


# === SENTIMIENTO (OPCIONAL) ===

def add_sentiment_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade columnas de sentimiento usando pysentimiento, si está instalado.
    Si no, deja el dataframe igual y muestra un aviso.
    """
    try:
        from pysentimiento import create_analyzer
    except ImportError:
        print("pysentimiento no está instalado. "
              "Ejecuta 'pip install pysentimiento' para añadir sentimiento.")
        return df

    print("Calculando sentimiento con pysentimiento (esto puede tardar un poco)...")
    analyzer = create_analyzer(task="sentiment", lang="es")

    labels = []
    pos_scores = []
    neu_scores = []
    neg_scores = []

    for text in df["clean_text"].astype(str):
        res = analyzer.predict(text)
        labels.append(res.output)
        pos_scores.append(res.probas.get("POS", 0.0))
        neu_scores.append(res.probas.get("NEU", 0.0))
        neg_scores.append(res.probas.get("NEG", 0.0))

    df["sentiment_label"] = labels
    df["sentiment_pos"] = pos_scores
    df["sentiment_neu"] = neu_scores
    df["sentiment_neg"] = neg_scores

    print("Sentimiento añadido al dataframe.")
    return df

def add_emotion_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade columnas de emoción usando pysentimiento (joy, anger, sadness, fear).
    Si pysentimiento no está instalado, no hace nada.
    """
    try:
        from pysentimiento import create_analyzer
    except ImportError:
        print("pysentimiento no está instalado. "
              "Ejecuta 'pip install pysentimiento' para añadir emociones.")
        return df

    print("Calculando emociones con pysentimiento (puede tardar)...")
    analyzer = create_analyzer(task="emotion", lang="es")

    labels = []
    joy_scores = []
    anger_scores = []
    sadness_scores = []
    fear_scores = []

    for text in df["clean_text"].astype(str):
        res = analyzer.predict(text)

        labels.append(res.output)
        joy_scores.append(res.probas.get("joy", 0.0))
        anger_scores.append(res.probas.get("anger", 0.0))
        sadness_scores.append(res.probas.get("sadness", 0.0))
        fear_scores.append(res.probas.get("fear", 0.0))

    df["emotion_label"] = labels
    df["emotion_joy"] = joy_scores
    df["emotion_anger"] = anger_scores
    df["emotion_sadness"] = sadness_scores
    df["emotion_fear"] = fear_scores

    print("Emociones añadidas al dataframe.")
    return df

# === LOAD / FEATURES / SAVE ===

def load_clean_data() -> pd.DataFrame:
    """Carga tweets limpios desde CSV; si falla, desde SQLite."""
    if os.path.exists(CLEAN_CSV):
        print(f"Cargando datos limpios desde {CLEAN_CSV} ...")
        return pd.read_csv(CLEAN_CSV)

    print("No se encontró el CSV limpio, intentando leer desde SQLite...")
    if not os.path.exists(RAW_DB):
        raise FileNotFoundError(f"No se encontró la base de datos en {RAW_DB}")

    with sqlite3.connect(RAW_DB) as conn:
        df = pd.read_sql("SELECT * FROM tweets_clean", conn)
    return df


def build_features(df: pd.DataFrame, use_sentiment: bool = True) -> pd.DataFrame:
    """Genera todas las features a partir del dataframe de tweets limpios."""
    print("Generando features básicas...")

    # Tokens
    df["tokens"] = df["clean_text"].astype(str).apply(tokenize_pro)
    df["n_tokens"] = df["tokens"].apply(len)

    # Longitud en caracteres
    df["n_chars"] = df["clean_text"].astype(str).str.len()

    # Número de menciones y hashtags desde texto original (si existe)
    if "text" in df.columns:
        df["n_mentions"] = df["text"].astype(str).str.count(r"@\w+")
        df["n_hashtags"] = df["text"].astype(str).str.count(r"#\w+")
    else:
        df["n_mentions"] = 0
        df["n_hashtags"] = 0

    # Candidato a partir de source
    if "source" in df.columns:
        df["candidate"] = df["source"].astype(str).apply(source_to_candidate)
    else:
        df["candidate"] = "Otro"

    # Añadir sentimiento
    if use_sentiment:
        df = add_sentiment_features(df)
        df = add_emotion_features(df)
    else:
        print("Sentimiento y emociones desactivados (use_sentiment=False).")

    print("Features generadas.")
    return df


def save_features(df: pd.DataFrame) -> None:
    """Guarda el dataframe de features en CSV y en SQLite."""
    # CSV
    df.to_csv(FEATURES_CSV, index=False, encoding="utf-8")
    print(f"Features guardadas en {FEATURES_CSV}")

    # SQLite
    if os.path.exists(RAW_DB):
        with sqlite3.connect(RAW_DB) as conn:
            df.to_sql("tweets_features", conn, if_exists="replace", index=False)
        print("Tabla 'tweets_features' creada/actualizada en la base de datos.")
    else:
        print(f"No se encontró la base de datos {RAW_DB}, no se guardó tabla SQL.")


def main() -> None:
    print("Fase 3: Feature Engineering de tuits políticos")
    df_clean = load_clean_data()
    df_features = build_features(df_clean, use_sentiment=True)
    save_features(df_features)
    print("Fase 3 completada: dataset listo para análisis avanzado y dashboard.")


if __name__ == "__main__":
    main()
