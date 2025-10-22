# src/data/clean.py
"""
Limpieza y preprocesamiento de tuits.
Lee desde la base de datos local (SQLite) y genera un CSV limpio.
"""

import re
import os
import pandas as pd
import sqlite3
import unicodedata

RAW_DB = "data/raw/twitter_data.db"
OUTPUT_CSV = "data/processed/tweets_clean.csv"

# Crear carpeta de salida si no existe
os.makedirs("data/processed", exist_ok=True)

def remove_emojis(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def normalize_text(text):
    text = text.lower()
    text = re.sub(r"http\S+", "", text)  # eliminar URLs
    text = re.sub(r"@\w+", "", text)  # eliminar menciones
    text = re.sub(r"#\w+", "", text)  # eliminar hashtags
    text = re.sub(r"[^a-záéíóúüñ0-9\s]", " ", text)  # quitar símbolos
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")  # quitar tildes
    text = re.sub(r"\s+", " ", text).strip()  # espacios extra
    return text

def clean_tweets(df):
    print("🧹 Limpiando tuits...")
    df["clean_text"] = df["text"].astype(str).apply(remove_emojis).apply(normalize_text)
    df = df.drop_duplicates(subset=["clean_text"])
    df = df[df["clean_text"].str.len() > 20]  # eliminar textos cortos
    df = df.reset_index(drop=True)
    print(f"✅ {len(df)} tuits limpios listos para análisis.")
    return df

def main():
    print("📂 Cargando datos desde la base de datos...")
    conn = sqlite3.connect(RAW_DB)
    df = pd.read_sql("SELECT id, text, created_at, source FROM tweets", conn)
    conn.close()

    df_clean = clean_tweets(df)

    # Guardar CSV limpio
    df_clean.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"💾 Archivo limpio guardado en: {OUTPUT_CSV}")

    # Guardar también en la base si quieres
    conn = sqlite3.connect(RAW_DB)
    df_clean.to_sql("tweets_clean", conn, if_exists="replace", index=False)
    conn.close()
    print("📦 Tabla 'tweets_clean' creada en la base de datos.")

if __name__ == "__main__":
    main()
