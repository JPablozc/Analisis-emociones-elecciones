"""
Scraper de X (Twitter) usando Playwright con inicio de sesión mediante cookies.
Permite acceder a tuits reales desde tu cuenta iniciada y guarda los resultados en SQLite.
"""

import time
import re
import json
from playwright.sync_api import sync_playwright
from src.data.database import init_db, insert_tweets

# Configuración general
DB_PATH = "data/raw/twitter_data.db"
HASHTAGS = ["EleccionesColombia", "Campañas2025", "DebatePresidencial",
            "Candidatos2025", "PartidoLiberal", "PartidoConservador",
            "IzquierdaColombiana", "DerechaColombiana",
            "Petro", "Fico", "Uribe", "Galán"]
MAX_RESULTS_PER_TAG = 100
COOKIES_PATH = "cookies_playwright.json"

def clean_text(text):
    """Limpia el texto del tuit eliminando URLs y espacios extra."""
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def scrape_hashtag(hashtag, max_results=50):
    """Abre X con Playwright, inicia sesión con cookies y extrae tuits recientes de un hashtag."""
    print(f"🔍 Buscando tuits para #{hashtag}...")

    tweets_data = []

    with sync_playwright() as p:
        # Lanzar navegador
        browser = p.chromium.launch(headless=False, slow_mo=250)
        context = browser.new_context()

        # Cargar cookies desde archivo JSON
        try:
            with open(COOKIES_PATH, "r", encoding="utf-8") as f:
                cookies = json.load(f)
                context.add_cookies(cookies)
                print("🍪 Sesión iniciada con cookies correctamente.")
        except Exception as e:
            print(f"⚠️ No se pudieron cargar las cookies: {e}")
            return []

        page = context.new_page()

        # Ir a la página de búsqueda del hashtag
        url = f"https://x.com/search?q=%23{hashtag}&src=typed_query&f=live"
        try:
    # Esperar solo al DOM inicial, no a toda la página
            page.goto(url, wait_until="domcontentloaded", timeout=120000)
            time.sleep(8)  # Esperar unos segundos para que se rendericen los tuits
        except Exception as e:
            print(f"⚠️ Advertencia: la página tardó demasiado en cargar ({e}). Continuando...")

        last_height = 0
        while len(tweets_data) < max_results:
            # Selector actualizado para texto de tuits
            tweets = page.locator("article div[data-testid='tweetText']").all_inner_texts()

            for t in tweets:
                clean_t = clean_text(t)
                if clean_t not in tweets_data and len(clean_t) > 30:
                    tweets_data.append(clean_t)
                    if len(tweets_data) >= max_results:
                        break

            # Scroll para cargar más resultados
            page.mouse.wheel(0, 4000)
            time.sleep(2.5)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        browser.close()

    print(f"✅ {len(tweets_data)} tuits recolectados para #{hashtag}.")
    return tweets_data


def main():
    print("✅ Script de Playwright iniciado.")
    init_db(DB_PATH)
    print("📦 Base de datos inicializada.")

    all_tweets = []

    for tag in HASHTAGS:
        tweets = scrape_hashtag(tag, MAX_RESULTS_PER_TAG)
        for i, text in enumerate(tweets):
            all_tweets.append({
                "id": f"{tag}_{i}",
                "author": "desconocido",
                "text": text,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "lang": "es",
                "source": f"#{tag}"
            })

    if all_tweets:
        insert_tweets(DB_PATH, all_tweets)
        print(f"🎯 {len(all_tweets)} tuits guardados correctamente en la base de datos local.")
    else:
        print("⚠️ No se recolectaron tuits. Verifica tus cookies o hashtags.")

if __name__ == "__main__":
    main()
