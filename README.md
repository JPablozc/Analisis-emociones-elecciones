# Análisis de Emociones Políticas en Redes Sociales (Twitter/X)

## Descripción general

Este proyecto tiene como propósito desarrollar una herramienta de ciencia de datos e inteligencia artificial que analice las emociones políticas expresadas en redes sociales, específicamente en Twitter (X).

El objetivo principal es medir cómo las emociones y sentimientos de los usuarios reflejan la percepción pública hacia candidatos, partidos o campañas políticas, y cómo estos indicadores pueden ser utilizados para evaluar el impacto emocional de estrategias electorales o comunicativas.

---

## Contexto

En la era digital, las redes sociales son el principal espacio donde las personas expresan y debaten sobre política.  
No solo se comparten ideas, sino que se construyen climas emocionales que influyen en la reputación pública, la intención de voto y la aceptación social.

Un caso emblemático fue el de las elecciones de Estados Unidos, donde se descubrió que campañas de desinformación en redes buscaron manipular emociones y generar desconfianza en el proceso electoral.  
Esto demuestra cómo la opinión pública puede ser afectada por la información (y la emoción) que circula en entornos digitales.

Frente a esto, este proyecto propone una herramienta analítica y ética, diseñada para comprender emociones, no manipularlas.

---

## Objetivo general

Analizar y modelar las emociones políticas expresadas en Twitter/X para evaluar la percepción ciudadana, identificar dinámicas de polarización afectiva y medir el impacto emocional de campañas electorales o de comunicación.

---

## Objetivos específicos

1. Recolectar datos de publicaciones políticas en Twitter/X, respetando principios éticos y de privacidad.  
2. Limpiar y anonimizar los datos, eliminando ruido, duplicados y cuentas automatizadas.  
3. Detectar emociones mediante modelos de procesamiento de lenguaje natural (PLN) e inteligencia artificial.  
4. Construir indicadores como:
   - Índice de Aprobación Emocional (IAE)
   - Polarización Afectiva (PA)
   - Ratio de Positividad (RP)
   - Volatilidad Emocional (VE)
5. Visualizar los resultados en un dashboard interactivo.  
6. Extender el modelo para medir campañas de marketing o comunicación institucional ajustando parámetros y público objetivo.

---

## Justificación

### Académica  
Contribuye al campo de la comunicación política digital, aplicando técnicas de análisis afectivo y minería de texto para entender las dinámicas emocionales del discurso público.

### Social  
Promueve la transparencia informativa y ayuda a comprender cómo los discursos en redes moldean percepciones colectivas.  
Permite identificar tendencias emocionales que pueden fortalecer o polarizar la conversación democrática.

### Aplicada  
Brinda una herramienta adaptable para:
- Evaluar campañas electorales en tiempo real.  
- Analizar reputación digital de instituciones o figuras públicas.  
- Medir impacto emocional de estrategias de comunicación o marketing.

---

## Metodología general

| Fase | Descripción | Resultados principales |
|------|-------------|------------------------|
| **1. Ingesta (Scraping)** | Extracción autenticada de tuits en tiempo real mediante Playwright y cookies. Scroll dinámico, captura de texto y metadatos. | Base de datos cruda en SQLite (`twitter_data.db`). |
| **2. Limpieza del texto** | Normalización, eliminación de ruido (URLs, emojis, menciones), deduplicación, tokenización inicial y estandarización. | `tweets_clean.csv` con texto preparado para análisis. |
| **3. Feature Engineering** | Tokenización avanzada, stopwords especializadas, extracción de n_tokens, n_chars, hashtags, menciones; mapeo hashtag → candidato; sentimiento (POS/NEU/NEG) y emociones (alegría/ira/tristeza/miedo). | `tweets_features.csv` con variables lingüísticas y emocionales. |
| **4. Topic Modeling (LDA)** | Vectorización optimizada, modelado de tópicos con LDA y asignación de `topic_id` a cada tuit. | `tweets_features_with_topics.csv` con temas políticos identificados. |
| **5. Dataset GOLD** | Integración final de texto limpio, sentimiento, emociones, temas y features numéricos. Cálculo de métricas diarias por candidato. | `tweets_gold.csv` y `candidate_daily_metrics.csv` (dataset maestro). |
| **6. Análisis exploratorio y estadístico** | Series temporales, distribución de emociones, nubes de palabras, comparaciones entre candidatos y temas, correlaciones. | Notebooks de análisis (`EDA`, `sentiment`, `topics`). |
| **7. Visualización interactiva** | Dashboard en Streamlit con filtros por candidato, fecha, tema, KPIs emocionales, gráficas dinámicas y nube de palabras. | Aplicación lista para presentación y análisis político. |

---

## Estructura del proyecto

Analisis-emociones-elecciones/
│
├── configs/
│   └── project.yaml
│
├── data/
│   ├── raw/
│   │   └── twitter_data.db
│   └── processed/
│       ├── candidate_daily_metrics.csv
│       ├── tweets_clean.csv
│       ├── tweets_features.csv
│       ├── tweets_features_with_topics.csv
│       ├── tweets_gold.csv
│       └── tweets_topics.csv
│
├── notebooks/
│   ├── 01_EDA.ipynb
│   ├── 02_sentiment_analysis.ipynb
│   └── 03_topic_modeling.ipynb
│
├── src/
│   ├── data/
│   │   ├── build_gold_dataset.py
│   │   ├── clean.py
│   │   ├── database.py
│   │   └── ingest_playwright.py
│   ├── features/
│   │   └── build_features.py
│   ├── models/
│   │   └── topic_modeling.py
│   └── visualization/
│       └── dashboard_app.py
│
├── cookies_playwright.json
├── requirements.txt
├── LICENSE
└── README.md

---
## 🚀 Tecnologías utilizadas

- **Python 3.10+**
- **Playwright** → extracción autenticada desde X  
- **SQLite** → almacenamiento de datos  
- **NLTK / PySentimiento** → NLP y análisis emocional  
- **scikit-learn** → Topic Modeling (LDA)  
- **Plotly / Streamlit** → visualización interactiva  
- **Matplotlib / WordCloud** → análisis exploratorio  

---

## Pipeline de análisis

### **Recolección de datos – Scraping con Playwright**
- Inicio de sesión mediante cookies.  
- Extracción desde hashtags, candidatos y términos políticos.  
- Scroll dinámico y captura de tuits reales.  
- Almacenamiento en SQLite.  

---

### **Limpieza avanzada del texto**
- Normalización (unicode, tildes, acentos).  
- Eliminación de ruido:
  - URLs  
  - menciones  
  - emojis  
  - símbolos  
- Deduplicación de tuits.  
- Generación de datos limpios listos para análisis.

---

### **Feature Engineering**
- Tokenización avanzada específica para análisis político.  
- Stopwords enriquecidas.  
- Variables generadas:
  - n_tokens  
  - n_chars  
  - n_mentions  
  - n_hashtags  
- Sentimiento: **positivo, negativo, neutral**  
- Emociones: **alegría, ira, tristeza, miedo**  
- Identificación del candidato asociado.

---

### **Topic Modeling (LDA)**
- Vectorización optimizada para español.  
- Identificación de 8 temas políticos principales.  
- Inclusión del `topic_id` en cada tuit.

---

### **Dataset GOLD**
Un dataset final completo que integra:

- texto original y limpio  
- sentimiento  
- emociones  
- tema asignado  
- features numéricos  
- candidato  
- fecha  
- métricas agregadas diarias

---

### **Dashboard interactivo**
Incluye:

- Filtros dinámicos por candidato, fecha y tema  
- KPIs emocionales  
- Gráficos por candidato  
- Análisis temporal  
- Distribución de temas  
- Nube de palabras interactiva  

---

### Resultados clave

- Emociones predominantes para cada candidato.  
- Temas dominantes detectados por LDA.  
- Cambios emocionales en el tiempo.  
- Tensiones, polaridad y clima político.  
- Visualizaciones dinámicas y listas para sustentación académica.

---

## Estado actual del proyecto

| Módulo | Estado |
|--------|--------|
| Scraping | ✔ Finalizado |
| Limpieza | ✔ Finalizado |
| Feature Engineering | ✔ Finalizado |
| Sentimiento & Emociones | ✔ Finalizado |
| Topic Modeling | ✔ Finalizado |
| Dataset GOLD | ✔ Finalizado |
| Dashboard interactivo | ✔ Finalizado |
| Optimización continua | 🔧 En progreso |