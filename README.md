# 🧠 Análisis de Emociones Políticas en Redes Sociales (Twitter/X)

## 🎯 **Descripción general**

Este proyecto tiene como propósito desarrollar una **herramienta de ciencia de datos e inteligencia artificial** que analice las **emociones políticas expresadas en redes sociales**, específicamente en **Twitter (X)**.  

El objetivo principal es **medir cómo las emociones y sentimientos de los usuarios reflejan la percepción pública hacia candidatos, partidos o campañas políticas**, y cómo estos indicadores pueden ser utilizados para **evaluar el impacto emocional de estrategias electorales o comunicativas**.

---

## 💬 **Contexto**

En la era digital, las redes sociales son el principal espacio donde las personas **opinan y sienten la política**.  
No solo se debaten ideas, sino que se construyen climas emocionales que influyen en la **reputación pública, la intención de voto y la aceptación social**.

Un caso emblemático fue el de las **elecciones de Estados Unidos**, donde se descubrió que campañas de desinformación en redes buscaron **manipular emociones** y generar desconfianza en el proceso electoral.  
Esto demuestra cómo la opinión pública puede ser afectada por la información (y la emoción) que circula en redes.

Frente a esto, este proyecto propone una herramienta **ética y analítica**, diseñada para **comprender emociones, no manipularlas**.

---

## 🎯 **Objetivo general**

Analizar y modelar las emociones políticas expresadas en Twitter/X para **evaluar la percepción ciudadana**, identificar dinámicas de **polarización afectiva** y medir el **impacto emocional de campañas electorales o de comunicación**.

---

## 🧩 **Objetivos específicos**

1. **Recolectar** datos de publicaciones políticas en Twitter/X, respetando principios éticos y de privacidad.  
2. **Limpiar y anonimizar** los datos, eliminando bots y cuentas automatizadas.  
3. **Detectar emociones** mediante modelos de procesamiento de lenguaje natural (PLN) e inteligencia artificial.  
4. **Construir indicadores** como:
   - Índice de Aprobación Emocional (IAE)
   - Polarización Afectiva (PA)
   - Ratio de Positividad (RP)
   - Volatilidad Emocional (VE)
5. **Visualizar los resultados** en un dashboard interactivo.  
6. **Extender el modelo** para medir campañas de marketing o comunicación institucional ajustando parámetros y público objetivo.

---

## 🔍 **Justificación**

### 📚 Académica  
Contribuye al campo de la **comunicación política digital**, aplicando técnicas de **análisis afectivo y minería de texto** para entender las dinámicas emocionales del discurso público.

### 🌍 Social  
Promueve la **transparencia informativa** y ayuda a comprender cómo los discursos en redes moldean percepciones colectivas.  
Permite identificar **tendencias emocionales** que pueden fortalecer o polarizar la conversación democrática.

### ⚙️ Aplicada  
Brinda una herramienta adaptable para:
- Evaluar campañas electorales en tiempo real.  
- Analizar reputación digital de instituciones o figuras públicas.  
- Medir impacto emocional de estrategias de comunicación o marketing.

---

## 🧠 **Metodología general**

| Fase | Descripción | Resultado esperado |
|------|--------------|--------------------|
| **1. Extracción** | Recolección de tuits relevantes (hashtags, menciones, partidos, candidatos). | Dataset crudo en `data/raw/`. |
| **2. Limpieza y filtrado** | Normalización de texto, eliminación de ruido, detección de bots, anonimización. | Datos limpios en `data/processed/`. |
| **3. Análisis emocional** | Aplicación de modelos de IA y PLN para detectar emociones y sentimientos. | Base con etiquetas emocionales. |
| **4. Indicadores e interpretación** | Cálculo de métricas agregadas (IAE, PA, RP, VE). | Métricas interpretables por grupo o periodo. |
| **5. Visualización** | Creación de dashboard interactivo (Plotly/Dash o Power BI). | Visualización del clima emocional. |
| **6. Reporte ético** | Publicación de hojas de datos, modelos y buenas prácticas. | Documentación en `docs/ethics/`. |