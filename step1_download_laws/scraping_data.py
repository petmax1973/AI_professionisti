
import os
import time
import logging
from collections import deque
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAZIONE ---
DOMAIN = "https://www.agenziaentrate.gov.it"
START_URL = f"{DOMAIN}/portale/web/guest/normativa-e-prassi"

# Sezioni del sito da esplorare (prefissi URL da seguire)
ALLOWED_PREFIXES = [
    f"{DOMAIN}/portale/normativa-e-prassi",
    f"{DOMAIN}/portale/web/guest/normativa-e-prassi",
    f"{DOMAIN}/portale/web/guest/archivio/normativa-prassi",
]

DOWNLOAD_BASE_DIR = "archivio_agenzia_entrate"
WAIT_BETWEEN_DOWNLOADS = 10  # Secondi di attesa tra un download e l'altro
PAGE_LOAD_TIMEOUT = 15       # Secondi max di attesa per il caricamento della pagina
MAX_DEPTH = 50               # Profondità massima di navigazione
# ----------------------

# Estensioni di documenti da scaricare
DOWNLOADABLE_EXTENSIONS = ('.pdf', '.doc', '.docx', '.xls', '.xlsx')

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraping_data.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)
# ---------------


def create_driver():
    """Crea e restituisce un'istanza del browser Chrome in modalità headless."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options,
    )
    return driver


def normalize_url(url):
    """Normalizza un URL rimuovendo frammenti (#) e query string (?)."""
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def is_document_url(url):
    """Verifica se un URL punta a un documento scaricabile.

    Gestisce anche URL come:
      .../file.pdf/uuid?t=12345
    dove l'estensione non è alla fine dell'URL.
    """
    parsed = urlparse(url)
    path = parsed.path.lower()
    # Controlla se una delle estensioni appare nel path
    for ext in DOWNLOADABLE_EXTENSIONS:
        if ext in path:
            return True
    return False


def extract_filename_from_url(url):
    """Estrae il nome del file da un URL, anche se ha segmenti extra dopo l'estensione."""
    parsed = urlparse(url)
    path = parsed.path

    # Cerca l'ultimo segmento che contiene un'estensione nota
    segments = path.split("/")
    for segment in reversed(segments):
        for ext in DOWNLOADABLE_EXTENSIONS:
            if ext in segment.lower():
                # Prende la parte fino all'estensione (inclusa)
                idx = segment.lower().find(ext)
                return segment[: idx + len(ext)]
    # Fallback: ultimo segmento del path
    return segments[-1] if segments[-1] else None


def get_local_folder(file_url):
    """Determina la cartella locale per salvare un file dato il suo URL.

    Rimuove dal path il segmento che contiene l'estensione del documento
    e tutti i segmenti successivi (es. UUID), così da non creare cartelle
    spurie con il nome del file.
    """
    parsed = urlparse(file_url)
    segments = parsed.path.strip("/").split("/")

    # Trova il primo segmento che contiene un'estensione nota e tronca lì
    clean_segments = []
    for seg in segments:
        if any(ext in seg.lower() for ext in DOWNLOADABLE_EXTENSIONS):
            break
        clean_segments.append(seg)

    dir_part = "/".join(clean_segments) if clean_segments else ""
    return os.path.join(DOWNLOAD_BASE_DIR, dir_part)


def download_file(file_url):
    """Scarica il file fisico mantenendo la struttura delle cartelle."""
    local_folder = get_local_folder(file_url)
    os.makedirs(local_folder, exist_ok=True)

    file_name = extract_filename_from_url(file_url)
    if not file_name:
        logger.warning("Impossibile estrarre il nome file da: %s", file_url)
        return

    full_local_path = os.path.join(local_folder, file_name)

    if os.path.exists(full_local_path):
        logger.info("[SKIP] File già presente: %s", file_name)
        return

    try:
        logger.info("[DOWNLOAD] Scaricando: %s ...", file_name)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(file_url, headers=headers, timeout=30)
        response.raise_for_status()

        with open(full_local_path, "wb") as f:
            f.write(response.content)

        logger.info("[OK] Salvato in: %s (%d bytes)", full_local_path, len(response.content))
        logger.info("[WAIT] Attesa di %d secondi...", WAIT_BETWEEN_DOWNLOADS)
        time.sleep(WAIT_BETWEEN_DOWNLOADS)

    except requests.exceptions.HTTPError as e:
        logger.error("[ERRORE HTTP] %s — Status: %s", file_url, e.response.status_code)
    except Exception as e:
        logger.error("[ERRORE] Download fallito per %s: %s", file_url, e)


def is_allowed_url(url):
    """Verifica se un URL rientra nelle sezioni che si vogliono esplorare."""
    return any(url.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def crawl(driver, start_url):
    """Naviga iterativamente nelle pagine usando una coda (BFS)."""
    visited_urls = set()
    queue = deque()
    queue.append((start_url, 0))
    download_count = 0

    while queue:
        url, depth = queue.popleft()
        url = normalize_url(url)

        if url in visited_urls:
            continue
        if depth > MAX_DEPTH:
            logger.warning("[MAX DEPTH] Profondità massima raggiunta per: %s", url)
            continue

        visited_urls.add(url)
        logger.info("[SCAN] (depth=%d, queue=%d, downloaded=%d) Esaminando: %s",
                     depth, len(queue), download_count, url)

        try:
            driver.get(url)
            WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            elements = driver.find_elements(By.TAG_NAME, "a")
            found_links = [
                el.get_attribute("href")
                for el in elements
                if el.get_attribute("href")
            ]

            for link in set(found_links):
                full_url = urljoin(url, link)

                # Se è un documento scaricabile, lo scarica
                if is_document_url(full_url):
                    download_file(full_url)
                    download_count += 1

                # Se è una sottopagina nelle sezioni consentite, la aggiunge alla coda
                else:
                    clean_url = normalize_url(full_url)
                    if is_allowed_url(clean_url) and clean_url not in visited_urls:
                        queue.append((clean_url, depth + 1))

        except Exception as e:
            logger.error("[ERRORE] Impossibile scansionare %s: %s", url, e)

    logger.info("[COMPLETATO] Pagine visitate: %d, Documenti scaricati: %d",
                len(visited_urls), download_count)


if __name__ == "__main__":
    driver = create_driver()
    try:
        logger.info("Inizio scansione iterativa. Premere CTRL+C per interrompere.")
        crawl(driver, START_URL)
    except KeyboardInterrupt:
        logger.info("[STOP] Interrotto dall'utente.")
    finally:
        driver.quit()
        logger.info("Processo terminato.")