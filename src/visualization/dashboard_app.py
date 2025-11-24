# src/visualization/dashboard_app.py
"""
Dashboard interactivo para el análisis de emociones y temas
en las elecciones presidenciales de Colombia 2026.

Lee:
- data/processed/tweets_gold.csv
- data/processed/candidate_daily_metrics.csv

Muestra:
- KPIs por candidato
- Distribución de sentimiento
- Evolución temporal del sentimiento
- Distribución de temas (topics)
- Nube de palabras filtrada
"""

import os
from typing import Tuple, List

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt


GOLD_CSV = "data/processed/tweets_gold.csv"
AGG_CSV = "data/processed/candidate_daily_metrics.csv"


# =========================
# CARGA DE DATOS (CACHEADA)
# =========================

@st.cache_data
def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    if not os.path.exists(GOLD_CSV):
        st.error(f"No se encontró {GOLD_CSV}. Ejecuta antes Fase 6 (build_gold_dataset.py).")
        st.stop()

    df_gold = pd.read_csv(GOLD_CSV)

    # Parseo de fechas
    if "created_at" in df_gold.columns:
        df_gold["created_at"] = pd.to_datetime(df_gold["created_at"], errors="coerce")
    if "date" in df_gold.columns:
        df_gold["date"] = pd.to_datetime(df_gold["date"], errors="coerce")

    if os.path.exists(AGG_CSV):
        df_agg = pd.read_csv(AGG_CSV)
        if "date" in df_agg.columns:
            df_agg["date"] = pd.to_datetime(df_agg["date"], errors="coerce")
    else:
        df_agg = pd.DataFrame()

    return df_gold, df_agg


# ===========
# UTILIDADES
# ===========

def compute_kpis(df: pd.DataFrame) -> dict:
    """Calcula KPIs básicos sobre el subconjunto filtrado."""
    n_tweets = len(df)

    sentiment_score = df["sentiment_score"].mean() if "sentiment_score" in df.columns else np.nan

    kpis = {
        "n_tweets": n_tweets,
        "sentiment_score": sentiment_score,
        "pct_pos": np.nan,
        "pct_neg": np.nan,
        "pct_neu": np.nan,
    }

    if "sentiment_label" in df.columns and n_tweets > 0:
        counts = df["sentiment_label"].value_counts(normalize=True)
        kpis["pct_pos"] = counts.get("POS", 0.0)
        kpis["pct_neg"] = counts.get("NEG", 0.0)
        kpis["pct_neu"] = counts.get("NEU", 0.0)

    return kpis


def plot_wordcloud(texts: List[str], title: str = "Nube de palabras"):
    """Genera una nube de palabras a partir de una lista de textos."""
    if not texts:
        st.info("No hay texto disponible para generar la nube de palabras.")
        return

    joined_text = " ".join(str(t) for t in texts if isinstance(t, str))

    if not joined_text.strip():
        st.info("El texto filtrado está vacío después de limpieza.")
        return

    wc = WordCloud(
        width=1000,
        height=500,
        background_color="white",
        colormap="viridis",
        max_words=200
    ).generate(joined_text)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(title)
    st.pyplot(fig)


# ===========
# MAIN APP
# ===========

def main():
    st.set_page_config(
        page_title="Análisis emociones elecciones 2026 – Colombia",
        layout="wide"
    )

    st.title("Análisis de emociones y temas – Elecciones Colombia 2026")

    df_gold, df_agg = load_data()

    # =========================
    # SIDEBAR: FILTROS
    # =========================
    st.sidebar.header("Filtros")

    # Candidatos
    candidates = sorted(df_gold["candidate"].dropna().unique().tolist())
    default_candidates = candidates  # todos por defecto
    selected_candidates = st.sidebar.multiselect(
        "Candidatos",
        options=candidates,
        default=default_candidates
    )

    # Rango de fechas
    if "date" in df_gold.columns and df_gold["date"].notna().any():
        min_date = df_gold["date"].min()
        max_date = df_gold["date"].max()
        date_range = st.sidebar.date_input(
            "Rango de fechas",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
        if isinstance(date_range, list) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = min_date
            end_date = max_date
    else:
        start_date = None
        end_date = None

    # Topic filter (si existe)
    topic_options = None
    selected_topics = None
    if "topic_id" in df_gold.columns:
        topic_options = sorted(df_gold["topic_id"].dropna().unique().tolist())
        topic_options_str = [str(t) for t in topic_options]
        selected_topics_str = st.sidebar.multiselect(
            "Temas (topic_id)",
            options=topic_options_str,
            default=topic_options_str
        )
        selected_topics = [int(t) for t in selected_topics_str] if selected_topics_str else []

    # =========================
    # APLICAR FILTROS
    # =========================
    df_filtered = df_gold.copy()

    if selected_candidates:
        df_filtered = df_filtered[df_filtered["candidate"].isin(selected_candidates)]

    if start_date is not None and end_date is not None and "date" in df_filtered.columns:
        mask = (df_filtered["date"] >= pd.to_datetime(start_date)) & (df_filtered["date"] <= pd.to_datetime(end_date))
        df_filtered = df_filtered[mask]

    if selected_topics is not None and "topic_id" in df_filtered.columns:
        if len(selected_topics) > 0:
            df_filtered = df_filtered[df_filtered["topic_id"].isin(selected_topics)]

    if df_filtered.empty:
        st.warning("No hay datos para los filtros seleccionados. Ajusta la selección.")
        return

    # =========================
    # KPIs
    # =========================
    kpis = compute_kpis(df_filtered)

    st.subheader("Indicadores clave (KPIs)")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tweets filtrados", f"{kpis['n_tweets']:,}")
    col2.metric("Sentiment score promedio", f"{kpis['sentiment_score']:.3f}" if not pd.isna(kpis['sentiment_score']) else "N/A")
    col3.metric("% Positivos", f"{kpis['pct_pos']*100:.1f}%" if not pd.isna(kpis['pct_pos']) else "N/A")
    col4.metric("% Negativos", f"{kpis['pct_neg']*100:.1f}%" if not pd.isna(kpis['pct_neg']) else "N/A")

    st.markdown("---")

    # =========================
    # GRÁFICO 1: Sentimiento por candidato (barras)
    # =========================
    st.subheader("Distribución de sentimiento por candidato")

    if "sentiment_label" in df_filtered.columns:
        fig_sent = px.histogram(
            df_filtered,
            x="candidate",
            color="sentiment_label",
            barmode="group",
            title="Conteo de tweets por candidato y sentimiento"
        )
        fig_sent.update_layout(xaxis_title="Candidato", yaxis_title="Número de tweets")
        st.plotly_chart(fig_sent, use_container_width=True)
    else:
        st.info("No se encontró la columna 'sentiment_label' en el dataset GOLD.")

    st.markdown("---")

    # =========================
    # GRÁFICO 2: Evolución temporal del sentimiento
    # =========================
    st.subheader("Evolución temporal del sentimiento promedio")

    if not df_agg.empty:
        df_agg_f = df_agg.copy()

        if selected_candidates:
            df_agg_f = df_agg_f[df_agg_f["candidate"].isin(selected_candidates)]
        if start_date is not None and end_date is not None:
            mask_agg = (df_agg_f["date"] >= pd.to_datetime(start_date)) & (df_agg_f["date"] <= pd.to_datetime(end_date))
            df_agg_f = df_agg_f[mask_agg]

        if not df_agg_f.empty:
            fig_ts = px.line(
                df_agg_f,
                x="date",
                y="mean_sentiment",
                color="candidate",
                title="Sentiment score promedio por día y candidato",
                markers=True
            )
            fig_ts.update_layout(xaxis_title="Fecha", yaxis_title="Sentiment score")
            st.plotly_chart(fig_ts, use_container_width=True)
        else:
            st.info("No hay datos agregados para los filtros seleccionados.")
    else:
        st.info("No se encontró candidate_daily_metrics.csv. Ejecuta Fase 6 para generarlo.")

    st.markdown("---")

    # =========================
    # GRÁFICO 3: Distribución de temas
    # =========================
    if "topic_id" in df_filtered.columns:
        st.subheader("Distribución de temas (Topic IDs)")

        # Serie de topics -> dataframe con columnas [topic_id, count]
        topic_counts = (
            df_filtered["topic_id"]
            .value_counts()
            .reset_index(name="count")          # la columna nueva se llama 'count'
            .rename(columns={"index": "topic_id"})
            .sort_values("topic_id")
        )

        fig_topics = px.bar(
            topic_counts,
            x="topic_id",
            y="count",
            title="Número de tweets por tema (topic_id)",
        )
        fig_topics.update_layout(xaxis_title="Topic ID", yaxis_title="Número de tweets")
        st.plotly_chart(fig_topics, use_container_width=True)
    else:
        st.info("Este dataset no contiene 'topic_id'. Ejecuta la Fase 5 (topic_modeling.py) para añadir temas.")

    # =========================
    # NUBE DE PALABRAS
    # =========================
    st.subheader("Nube de palabras")

    # Usamos 'clean_text' del df filtrado
    texts_for_wc = df_filtered["clean_text"].dropna().tolist()
    plot_wordcloud(texts_for_wc, title="Nube de palabras – datos filtrados")


if __name__ == "__main__":
    main()
