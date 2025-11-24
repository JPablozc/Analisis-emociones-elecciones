# src/data/clean.py
"""
Limpieza y preprocesamiento de tuits.
Lee desde la base de datos local (SQLite) y genera un CSV limpio.
"""

import re
import os
import pandas as pd
import sqlite3

RAW_DB = "data/raw/twitter_data.db"
OUTPUT_CSV = "data/processed/tweets_clean.csv"
MIN_LEN = 20  # longitud mínima del texto limpio

# Crear carpeta de salida si no existe
os.makedirs("data/processed", exist_ok=True)


def remove_emojis(text: str) -> str:
    emoji_pattern = re.compile("[" 
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub("", text)


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+", "", text)        # eliminar URLs
    text = re.sub(r"@\w+", "", text)           # eliminar menciones
    text = re.sub(r"#\w+", "", text)           # eliminar hashtags
    text = re.sub(r"[^a-záéíóúüñ0-9\s]", " ", text)  # quitar símbolos raros
    text = re.sub(r"\s+", " ", text).strip()   # espacios extra
    return text


def clean_tweets(df: pd.DataFrame) -> pd.DataFrame:
    print("Limpiando tuits...")
    df["clean_text"] = (
        df["text"]
        .astype(str)
        .apply(remove_emojis)
        .apply(normalize_text)
    )

    # Eliminar duplicados por texto limpio
    df = df.drop_duplicates(subset=["clean_text"])

    # Eliminar textos muy cortos
    df = df[df["clean_text"].str.len() > MIN_LEN]

    df = df.reset_index(drop=True)
    print(f"{len(df)} tuits limpios listos para análisis.")
    return df


def main() -> None:
    print("Cargando datos desde la base de datos...")

    with sqlite3.connect(RAW_DB) as conn:
        # trae también categoria (ajústalo a las columnas reales de tu tabla)
        df = pd.read_sql(
             "SELECT * FROM tweets",
            conn
        )

    df_clean = clean_tweets(df)

    # Guardar CSV limpio
    df_clean.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"Archivo limpio guardado en: {OUTPUT_CSV}")

    # Guardar también en la base como tabla limpia
    with sqlite3.connect(RAW_DB) as conn:
        df_clean.to_sql("tweets_clean", conn, if_exists="replace", index=False)
    print("Tabla 'tweets_clean' creada en la base de datos.")


if __name__ == "__main__":
    main()
