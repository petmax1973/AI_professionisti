
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

# Punti di partenza multipli per coprire sia la sezione corrente che l'archivio
START_URLS = [
    f"{DOMAIN}/portale/web/guest/archivio/normativa-prassi-archivio-documentazione/provvedimenti/provvedimenti-soggetti",
    f"{DOMAIN}/portale/web/guest/normativa-e-prassi/circolari/archivio-circolari",
    f"{DOMAIN}/portale/web/guest/normativa-e-prassi/risoluzioni/archivio-risoluzioni",
    f"{DOMAIN}/portale/normativa-e-prassi/risposte-agli-interpelli/interpelli/archivio-interpelli",
    f"{DOMAIN}/portale/normativa-e-prassi/risposte-agli-interpelli/risposte-alle-istanze-di-consulenza-giuridica/archivio-risposte-alle-istanze-di-consulenza-giuridica",
]

# Sezioni del sito da esplorare (prefissi URL da seguire)
ALLOWED_PREFIXES = []
for url in START_URLS:
    ALLOWED_PREFIXES.append(url)
    if "/web/guest/" in url:
        ALLOWED_PREFIXES.append(url.replace("/web/guest/", "/"))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_BASE_DIR = os.path.join(SCRIPT_DIR, "archivio_agenzia_entrate")
WAIT_BETWEEN_DOWNLOADS = 10  # Secondi di attesa tra un download e l'altro
PAGE_LOAD_TIMEOUT = 15       # Secondi max di attesa per il caricamento della pagina
MAX_DEPTH = 50               # Profondità massima di navigazione
MAX_DOWNLOAD_RETRIES = 3     # Tentativi max per download singolo file
MAX_SCAN_RETRIES = 2         # Tentativi max per scansione pagina
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


def get_local_folder(page_url):
    """Determina la cartella locale per salvare un file basata sull'URL della pagina.

    I nomi delle cartelle coincidono con la struttura del percorso del sito web.
    """
    parsed = urlparse(page_url)
    path = parsed.path.strip("/")
    return os.path.join(DOWNLOAD_BASE_DIR, path)


def download_file(file_url, page_url):
    """Scarica il file fisico mantenendo la struttura delle cartelle del sito.

    Include un meccanismo di retry con backoff esponenziale.
    """
    local_folder = get_local_folder(page_url)
    os.makedirs(local_folder, exist_ok=True)

    file_name = extract_filename_from_url(file_url)
    if not file_name:
        logger.warning("Impossibile estrarre il nome file da: %s", file_url)
        return

    full_local_path = os.path.join(local_folder, file_name)

    if os.path.exists(full_local_path):
        logger.info("[SKIP] File già presente: %s", file_name)
        return

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for attempt in range(1, MAX_DOWNLOAD_RETRIES + 1):
        try:
            logger.info("[DOWNLOAD] Scaricando: %s (tentativo %d/%d) ...",
                        file_name, attempt, MAX_DOWNLOAD_RETRIES)
            response = requests.get(file_url, headers=headers, timeout=60)
            response.raise_for_status()

            with open(full_local_path, "wb") as f:
                f.write(response.content)

            logger.info("[OK] Salvato in: %s (%d bytes)",
                        full_local_path, len(response.content))
            logger.info("[WAIT] Attesa di %d secondi...", WAIT_BETWEEN_DOWNLOADS)
            time.sleep(WAIT_BETWEEN_DOWNLOADS)
            return  # Download riuscito, esci

        except requests.exceptions.HTTPError as e:
            logger.error("[ERRORE HTTP] %s — Status: %s",
                         file_url, e.response.status_code)
            return  # Errore HTTP non recuperabile, non ritentare
        except Exception as e:
            wait_time = WAIT_BETWEEN_DOWNLOADS * (2 ** (attempt - 1))
            if attempt < MAX_DOWNLOAD_RETRIES:
                logger.warning("[RETRY] Download fallito per %s: %s — "
                               "Ritento tra %d secondi (tentativo %d/%d)",
                               file_url, e, wait_time, attempt,
                               MAX_DOWNLOAD_RETRIES)
                time.sleep(wait_time)
            else:
                logger.error("[ERRORE] Download fallito definitivamente "
                             "per %s dopo %d tentativi: %s",
                             file_url, MAX_DOWNLOAD_RETRIES, e)


def is_allowed_url(url):
    """Verifica se un URL rientra nelle sezioni che si vogliono esplorare."""
    return any(url.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def crawl(driver, start_urls):
    """Naviga iterativamente nelle pagine usando una coda (BFS).

    Accetta una lista di URL di partenza e include un meccanismo
    di retry per la scansione delle pagine.
    """
    visited_urls = set()
    queue = deque()
    for url in start_urls:
        queue.append((url, 0))
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

        found_links = []
        scan_success = False

        for attempt in range(1, MAX_SCAN_RETRIES + 1):
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
                scan_success = True
                break  # Scansione riuscita, esci dal retry

            except Exception as e:
                if attempt < MAX_SCAN_RETRIES:
                    logger.warning(
                        "[RETRY SCAN] Errore scansione %s: %s — "
                        "Ritento (tentativo %d/%d)",
                        url, e, attempt, MAX_SCAN_RETRIES)
                    time.sleep(5)
                else:
                    logger.error(
                        "[ERRORE] Impossibile scansionare %s dopo %d "
                        "tentativi: %s", url, MAX_SCAN_RETRIES, e)

        if not scan_success:
            continue

        for link in set(found_links):
            full_url = urljoin(url, link)

            # Se è un documento scaricabile, lo scarica
            if is_document_url(full_url):
                download_file(full_url, url)
                download_count += 1

            # Se è una sottopagina nelle sezioni consentite, la aggiunge alla coda
            else:
                clean_url = normalize_url(full_url)
                if is_allowed_url(clean_url) and clean_url not in visited_urls:
                    queue.append((clean_url, depth + 1))

    logger.info("[COMPLETATO] Pagine visitate: %d, Documenti scaricati: %d",
                len(visited_urls), download_count)


if __name__ == "__main__":
    driver = create_driver()
    try:
        logger.info("Inizio scansione iterativa con %d URL di partenza. "
                    "Premere CTRL+C per interrompere.", len(START_URLS))
        crawl(driver, START_URLS)
    except KeyboardInterrupt:
        logger.info("[STOP] Interrotto dall'utente.")
    finally:
        driver.quit()
        logger.info("Processo terminato.")