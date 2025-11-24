"""
Scraper de X (Twitter) usando Playwright con inicio de sesión mediante cookies.
Permite acceder a tuits reales desde tu cuenta iniciada y guarda los resultados en SQLite.
"""

import time
import re
import json
import random
from typing import List, Dict, Any

from playwright.sync_api import sync_playwright, BrowserContext, Page
from src.data.database import init_db, insert_tweets

# Configuración general
DB_PATH = "data/raw/twitter_data.db"

HASHTAGS = [
    # CANDIDATOS OFICIALES
    "IvanCepeda", "CepedaPresidente", "Cepeda",
    "LuisGilbertoMurillo", "MurilloPresidente", "Murillo2026",

    # PRECANDIDATOS
    "MariaFernandaCabal", "CabalPresidenta", "Cabal", "Cabal2026",
    "ClaudiaLopez", "LopezPresidenta", "ClaudiaLopez2026",
    "GustavoBolivar", "BolivarPresidente", "Bolivar2026",
    "AndresGuerra", "AndresGuerra2026",

    # FIGURAS POLÉMICAS (NO candidatos pero relevantes)
    "Petro", "GustavoPetro", "PetroColombia",
    "Uribe", "AlvaroUribe", "Uribistas",
    "VickyDavila", "Davila", "VickyDavilaColombia",
    "DanielQuintero", "QuinteroCalle",
    "PoloPolo", "MiguelPoloPolo", "PoloPoloColombia",
    "RodolfoHernandez", "RodolfoHernandezColombia",

    # GENERALES (coyuntura política nacional)
    "EleccionesColombia2026",
    "ColombiaDecide",
    "ColombiaElige2026",
    "DebatePresidencial",
    "PoliticaColombiana"
]

MAX_RESULTS_PER_TAG = 50 #prueba

COOKIES_PATH = "cookies_playwright.json"

CATEGORIES = {
    # CANDIDATOS
    "IvanCepeda": "Candidato",
    "CepedaPresidente": "Candidato",
    "LuisGilbertoMurillo": "Candidato",
    "MurilloPresidente": "Candidato",

    # PRECANDIDATOS
    "MariaFernandaCabal": "Precandidato",
    "CabalPresidenta": "Precandidato",
    "ClaudiaLopez": "Precandidato",
    "LopezPresidenta": "Precandidato",
    "GustavoBolivar": "Precandidato",
    "BolivarPresidente": "Precandidato",
    "AndresGuerra": "Precandidato",

    # POLÉMICOS
    "Petro": "Polemico",
    "GustavoPetro": "Polemico",
    "Uribe": "Polemico",
    "AlvaroUribe": "Polemico",
    "VickyDavila": "Polemico",
    "Davila": "Polemico",
    "DanielQuintero": "Polemico",
    "PoloPolo": "Polemico",
    "MiguelPoloPolo": "Polemico",
    "RodolfoHernandez": "Polemico",

    # GENERALES
    "EleccionesColombia2026": "General",
    "ColombiaDecide": "General",
    "ColombiaElige2026": "General",
    "DebatePresidencial": "General",
    "PoliticaColombiana": "General"
}

# Constantes de scraping
_URL_PATTERN = re.compile(r"http\S+")
TWEET_TEXT_SELECTOR = "article div[data-testid='tweetText']"
SCROLL_STEP = 4000

MAX_RETRIES_ERROR_PAGE = 3           # Reintentos cuando aparece "Algo salió mal"
BASE_RETRY_DELAY = 5.0               # Segundos base para backoff en recarga
SCROLL_BASE_DELAY = 2.0              # Segundos base entre scrolls
SCROLL_JITTER = 1.5                  # Aleatoriedad extra en el delay
BETWEEN_HASHTAGS_DELAY = (4, 9)      # Rango de pausa entre hashtags (min, max)

ERROR_TEXT_CANDIDATES = [
    "Algo salió mal",
    "Something went wrong",
    "Rate limit exceeded",
]


def clean_text(text: str) -> str:
    """Limpia el texto del tuit eliminando URLs y espacios extra."""
    if not isinstance(text, str):
        return ""
    text = _URL_PATTERN.sub("", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _load_cookies(path: str) -> List[Dict[str, Any]]:
    """Carga cookies desde un archivo JSON y las devuelve como lista."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    return data


def _page_has_error(page: Page) -> bool:
    """
    Revisa si la página muestra algún mensaje típico de error
    tipo 'Algo salió mal' o 'Something went wrong'.
    """
    try:
        body_text = page.inner_text("body")
    except Exception:
        return False

    if not body_text:
        return False

    body_text = body_text.strip()
    for candidate in ERROR_TEXT_CANDIDATES:
        if candidate in body_text:
            return True
    return False


def _try_recover_from_error(page: Page, url: str) -> bool:
    """
    Intenta recuperarse de una página en estado de error recargando
    algunas veces con backoff exponencial y jitter.
    Devuelve True si logra recuperar, False si sigue en error.
    """
    for attempt in range(1, MAX_RETRIES_ERROR_PAGE + 1):
        delay = BASE_RETRY_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 2.0)
        print(f"Página en estado de error. Esperando {delay:.1f}s antes de recargar (intento {attempt}/{MAX_RETRIES_ERROR_PAGE})...")
        page.wait_for_timeout(int(delay * 1000))

        try:
            page.reload(wait_until="domcontentloaded", timeout=130_000)
            page.wait_for_timeout(7_000 + int(random.uniform(0, 3_000)))
        except Exception as e:
            print(f"Error al recargar la página {url}: {e}")
            continue

        if not _page_has_error(page):
            print("Recuperado del estado de error.")
            return True

    print("No se pudo recuperar del estado de error tras varios intentos.")
    return False


def scrape_hashtag(hashtag: str, max_results: int = 50) -> List[str]:
    """Abre X con Playwright, inicia sesión con cookies y extrae tuits recientes de un hashtag."""
    print(f"\n🔍 Buscando tuits para #{hashtag}...")

    tweets_data: List[str] = []
    seen_texts = set()

    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(headless=False, slow_mo=250)
            context: BrowserContext = browser.new_context()

            # Cargar cookies desde archivo JSON
            try:
                cookies = _load_cookies(COOKIES_PATH)
                context.add_cookies(cookies)
                print("Sesión iniciada con cookies correctamente.")
            except Exception as e:
                print(f"No se pudieron cargar las cookies desde {COOKIES_PATH}: {e}")
                return []

            page: Page = context.new_page()

            url = f"https://x.com/search?q=%23{hashtag}&src=typed_query&f=live"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=130_000)
                # Espera aleatoria para que se carguen tuits
                initial_wait = random.uniform(7.0, 11.0)
                print(f"Esperando {initial_wait:.1f}s para cargar tuits iniciales...")
                page.wait_for_timeout(int(initial_wait * 1000))
            except Exception as e:
                print(f"Advertencia: la página tardó demasiado en cargar para #{hashtag} ({e}).")
                return []

            # Comprobar si la página está en estado de error
            if _page_has_error(page):
                print(f"X devolvió un estado de error inicial para #{hashtag}. Intentando recuperar...")
                recovered = _try_recover_from_error(page, url)
                if not recovered:
                    return []

            last_height = 0

            while len(tweets_data) < max_results:
                if _page_has_error(page):
                    print(f"Detectado estado de error durante el scroll de #{hashtag}. Parando scraping de este hashtag.")
                    break

                try:
                    tweets = page.locator(TWEET_TEXT_SELECTOR).all_inner_texts()
                except Exception as e:
                    print(f"Error al obtener tuits para #{hashtag}: {e}")
                    break

                if not tweets:
                    print(f"No se encontraron más tuits visibles para #{hashtag}.")
                    break

                for t in tweets:
                    clean_t = clean_text(t)
                    if clean_t and len(clean_t) > 30 and clean_t not in seen_texts:
                        seen_texts.add(clean_t)
                        tweets_data.append(clean_t)
                        if len(tweets_data) >= max_results:
                            break

                # Scroll para cargar más resultados con delay aleatorio
                delay = SCROLL_BASE_DELAY + random.uniform(0, SCROLL_JITTER)
                page.mouse.wheel(0, SCROLL_STEP)
                print(f"Scroll realizado. Esperando {delay:.2f}s antes del siguiente intento...")
                page.wait_for_timeout(int(delay * 1000))

                try:
                    new_height = page.evaluate("document.body.scrollHeight")
                except Exception:
                    print(f"No se pudo evaluar scrollHeight para #{hashtag}.")
                    break

                if new_height == last_height:
                    print(f"Altura de scroll sin cambios, finalizando scroll para #{hashtag}.")
                    break
                last_height = new_height

        finally:
            if browser is not None:
                browser.close()

    print(f"{len(tweets_data)} tuits recolectados para #{hashtag}.")
    return tweets_data


def main() -> None:
    print("Script de Playwright iniciado.")
    init_db(DB_PATH)
    print("Base de datos inicializada.")

    all_tweets: List[Dict[str, Any]] = []

    for tag in HASHTAGS:
        tweets = scrape_hashtag(tag, MAX_RESULTS_PER_TAG)
        if not tweets:
            print(f"No se obtuvieron tuits para #{tag}.")
        else:
            batch = []
            for i, text in enumerate(tweets):
                batch.append({
                    "id": f"{tag}_{i}",
                    "author": "desconocido",
                    "text": text,
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "lang": "es",
                    "source": f"#{tag}",
                    "categoria": CATEGORIES.get(tag, "General"),
                })

            # Guardar por hashtag para no perder progreso si algo falla más adelante
            insert_tweets(DB_PATH, batch)
            all_tweets.extend(batch)
            print(f"{len(batch)} tuits de #{tag} guardados en la base de datos.")

        # Pausa entre hashtags para no parecer tan bot
        pause = random.uniform(*BETWEEN_HASHTAGS_DELAY)
        print(f"⏸ Pausando {pause:.1f}s antes de pasar al siguiente hashtag...")
        time.sleep(pause)

    if all_tweets:
        print(f"En total se guardaron {len(all_tweets)} tuits en la base de datos local.")
    else:
        print("No se recolectaron tuits. Verifica tus cookies o hashtags.")


if __name__ == "__main__":
    main()
