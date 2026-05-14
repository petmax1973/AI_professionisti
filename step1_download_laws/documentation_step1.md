# Obiettivo dello Step 1: Acquisizione dei Dati Legali (Download)

> **Nota di automazione:** Se desideri eseguire questo step (assieme allo Step 2 e 3) in modo del tutto automatico e asincrono, fai riferimento allo script `run_pipeline.py` documentato nel README principale del progetto.

Questo step contiene **due script indipendenti** per l'acquisizione di documenti legali da fonti istituzionali italiane:

| Script              | Fonte                                                    | Formato output             |
|---------------------|----------------------------------------------------------|----------------------------|
| `export_laws_2.py`  | API Normattiva (banca dati statale)                      | JSON                       |
| `scraping_data.py`  | Sito Agenzia delle Entrate (sezione Normativa e Prassi)  | PDF, DOC, DOCX, XLS, XLSX  |

---

## Indice
- [Script 1: `export_laws_2.py` — Download leggi da Normattiva](#script-1-export_laws_2py--download-leggi-da-normattiva)
  - [Come funziona passo per passo](#come-funziona-passo-per-passo)
  - [Output](#output)
- [Script 2: `scraping_data.py` — Scraping Agenzia delle Entrate](#script-2-scraping_datapy--scraping-agenzia-delle-entrate)
  - [Come funziona lo scraping passo per passo](#come-funziona-lo-scraping-passo-per-passo)
  - [Configurazione](#configurazione)
  - [Dipendenze aggiuntive](#dipendenze-aggiuntive)
  - [Output dello scraping](#output-dello-scraping)
- [Come Eseguire gli Script (Requisiti e Installazione)](#come-eseguire-gli-script-requisiti-e-installazione)
  - [1. Installazione Generale (Linux / Windows / Cloud)](#1-installazione-generale-linux--windows--cloud)
  - [2. Installazione Specifica per Sistemi macOS](#2-installazione-specifica-per-sistemi-macos)
  - [3. Nota Specifica: MacBook Air M1 (8GB RAM)](#3-nota-specifica-macbook-air-m1-8gb-ram)
  - [4. Installazione Specifica per Raspberry Pi (ARM) e Acer Veriton gn100](#4-installazione-specifica-per-raspberry-pi-arm-e-acer-veriton-gn100)

---

## Script 1: `export_laws_2.py` — Download leggi da Normattiva

Lo script `export_laws_2.py` è il motore di acquisizione (crawler/downloader) del progetto. Il suo scopo esclusivo è interfacciarsi con le API pubbliche della banca dati statale "Normattiva", interrogare il sistema per trovare le leggi aggiornate e scaricarle in un formato strutturato (JSON) per la successiva elaborazione.

A differenza di uno scaricamento manuale, questo script automatizza la complessa "danza" asincrona richiesta dal server ministeriale per generare l'esportazione di una legge.

### Come funziona passo per passo

1. **Configurazione Parametrica Iniziale** — All'inizio del file sono definite delle costanti cruciali:
   - `EFFECTIVE_DATE` / `START_DATE_OF_ENACTMENT`: I filtri temporali per restringere il campo di ricerca.
   - `MAX_DOCS_PER_TYPE`: Limita il numero di documenti da scaricare per ogni tipologia (utile per test veloci o per scaricare solo le ultimissime novità). Se impostato su `None`, lo script attiverà la "Paginazione Automatica" e scaricherà TUTTI i documenti disponibili andando indietro nel tempo fino alla data di `START_DATE_OF_ENACTMENT`.
   - `ACT_TYPES`: Una lista esaustiva di 30 tipologie di atti (Costituzione, Leggi, Decreti Legislativi, DPCM, ecc.) che l'IA dovrà conoscere.

2. **Ricerca e Filtraggio Iniziale** — Per ognuno dei 30 tipi di atto legislativo definiti, lo script interroga l'API di "Ricerca Avanzata" (`ricerca/avanzata`). Richiede al server l'elenco dei documenti più recenti (fino a `MAX_DOCS_PER_TYPE`) e recupera una prima lista di metadati basilari (Titolo, Numero, Anno).

3. **Verifica di Esistenza (Idempotenza)** — Prima di avviare il pesante processo di download, lo script costruisce il nome del file finale (es. `legge_27_february_2026_n_26.json`). Se questo file è già presente sul disco (nella sua sotto-cartella specifica), lo script lo "salta" in modo intelligente. Questo significa che puoi eseguire lo script tutti i giorni, e scaricherà solo le nuove leggi emanate in quelle ultime 24 ore.

4. **Il Ciclo di Esportazione Asincrona (La "Danza" API)** — Se il file è una novità, lo script inizia la comunicazione con Normattiva. Il download richiede 4 passaggi di rete obbligatori:
   - **Richiesta di Estrazione**: Invia un payload specificando l'atto esatto, chiedendo al server di preparare un'esportazione in formato "JSON". Riceve indietro un "Token" di tracciamento.
   - **Conferma**: Invia una seconda chiamata per "confermare" l'avvio del lavoro.
   - **Polling (Attesa Attiva)**: Il server ministeriale impiega del tempo per generare il pacchetto. Lo script "bussa" periodicamente (ogni 4 secondi) a un endpoint di stato (`check-status`) finché il server non risponde che il pacchetto è pronto (stato "3").
   - **Download Reale**: Solo a questo punto avvia lo scaricamento vero e proprio dei dati.

5. **Estrazione Ottimizzata In-Memory (Zero IO Access)** — Il server del ministero restituisce sempre il file compresso dentro un archivio `.zip`. Invece di salvare il `.zip` sull'hard disk, lo script utilizza l'ottimizzazione `io.BytesIO()`: scarica l'archivio in RAM, lo scompatta al volo, estrae il file JSON e lo salva direttamente nel percorso finale (es. `documents_collection/legge/`).

> **In sintesi:** Lo script è un worker autonomo e resiliente. Interroga le API Statali, controlla se ci sono leggi nuove, gestisce l'intero ciclo asincrono di creazione del pacchetto sui server ministeriali, decodifica gli archivi compatti in RAM e deposita documenti legali in rigorosi file JSON divisi per categoria.

### Output

I documenti vengono salvati in:

```text
step1_download_laws/documents_collection/
├── legge/
│   ├── legge_27_february_2026_n_26.json
│   └── ...
├── decreto_legislativo/
│   └── ...
└── ...
```

---

## Script 2: `scraping_data.py` — Scraping Agenzia delle Entrate

Lo script `scraping_data.py` è un **web crawler iterativo** che naviga automaticamente la sezione "Normativa e Prassi" del sito dell'Agenzia delle Entrate e scarica tutti i documenti (PDF, DOC, DOCX, XLS, XLSX) pubblicati nelle sotto-sezioni: Circolari, Provvedimenti, Risoluzioni, Risposte agli Interpelli.

### Come funziona lo scraping passo per passo

1. **Navigazione BFS (Breadth-First Search)** — Lo script parte dalla pagina indice della sezione "Normativa e Prassi" e naviga iterativamente tutte le sotto-pagine usando una coda (`deque`), evitando la ricorsione che potrebbe causare stack overflow su siti grandi.

2. **Caricamento JavaScript** — Usa Selenium con Chrome in modalità headless per caricare le pagine che richiedono rendering JavaScript. Attende il caricamento del DOM tramite `WebDriverWait`.

3. **Riconoscimento documenti** — I link ai documenti sul sito dell'Agenzia delle Entrate hanno un formato particolare (es. `.../Circolare.pdf/uuid?t=timestamp`). Lo script cerca le estensioni note (`.pdf`, `.doc`, ecc.) all'interno del path URL, non solo alla fine.

4. **Download con controllo** — Per ogni documento trovato:
   - Verifica che il file non esista già localmente (idempotenza).
   - Controlla lo status HTTP della risposta (`raise_for_status()`).
   - Rispetta un'attesa di 10 secondi tra download (`WAIT_BETWEEN_DOWNLOADS`).

5. **Logging strutturato** — Tutte le operazioni vengono loggate con timestamp sia su console che su file (`scraping_data.log`).

### Configurazione

Le costanti configurabili all'inizio del file:

| Parametro                | Default                              | Descrizione                          |
|--------------------------|--------------------------------------|--------------------------------------|
| `DOMAIN`                 | `https://www.agenziaentrate.gov.it`  | Dominio del sito                     |
| `ALLOWED_PREFIXES`       | 3 prefissi URL                       | Sezioni del sito da esplorare        |
| `DOWNLOAD_BASE_DIR`      | `archivio_agenzia_entrate`           | Cartella di output                   |
| `WAIT_BETWEEN_DOWNLOADS` | `10` sec                             | Pausa tra un download e l'altro      |
| `PAGE_LOAD_TIMEOUT`      | `15` sec                             | Timeout caricamento pagina           |
| `MAX_DEPTH`              | `50`                                 | Profondità massima di navigazione    |

### Dipendenze aggiuntive

A differenza di `export_laws_2.py`, questo script richiede:

- **`selenium`** — Per il rendering JavaScript delle pagine web
- **`webdriver-manager`** — Per la gestione automatica di ChromeDriver
- **Google Chrome** — Deve essere installato sul sistema

Tutte le dipendenze Python sono dichiarate in `requirements.txt` e vengono installate automaticamente da `setup_env.sh`.

### Output dello scraping

I documenti vengono salvati in:

```text
step1_download_laws/archivio_agenzia_entrate/
├── portale/
│   └── documents/
│       └── 20143/
│           ├── 9680913/
│           │   └── Circolare_Terzo_Settore_n_1_del_19_febbraio_2026.pdf
│           ├── 8410829/
│           │   └── Circolare_Redditi_terreni_08.08.25.pdf
│           └── ...
```

> **Nota:** La cartella `archivio_agenzia_entrate/` è esclusa dal repository Git tramite `.gitignore`.

---

## Come Eseguire gli Script (Requisiti e Installazione)

Entrambi gli script condividono lo stesso ambiente virtuale (`venv`). Di seguito le istruzioni divise per tipologia di hardware.

### 1. Installazione Generale (Linux / Windows / Cloud)

Per eseguire gli script su un server cloud generico, una VPS Linux o un PC Windows:

1. Apri un terminale o prompt dei comandi.
2. Posizionati all'interno della cartella dello Step 1 (`cd step1_download_laws`).
3. **SOLO LA PRIMA VOLTA** - Crea l'ambiente e installa le dipendenze:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # (Su Windows: venv\Scripts\activate)
   pip install -r requirements.txt
   ```

4. **OGNI VOLTA CHE APRI UN NUOVO TERMINALE** - Attiva l'ambiente ed esegui lo script desiderato:

   ```bash
   source venv/bin/activate  # (Su Windows: venv\Scripts\activate)
   python3 export_laws_2.py       # Download leggi da Normattiva (JSON)
   python3 scraping_data.py       # Scraping Agenzia delle Entrate (PDF)
   ```

> **Attenzione (Requisiti di Sistema):** Mentre `export_laws_2.py` funziona in modo del tutto autonomo, lo script `scraping_data.py` utilizza Selenium. Pertanto è **strettamente necessario** che il browser Google Chrome (o Chromium) sia pre-installato sul sistema operativo prima di avviare l'esecuzione.

### 2. Installazione Specifica per Sistemi macOS

Se utilizzi un Mac (Intel o Apple Silicon M1/M2/M3/M4):

1. Apri l'app Terminale.
2. Posizionati all'interno della cartella dello Step 1:

   ```bash
   cd step1_download_laws
   ```

3. **Solo ed esclusivamente la prima volta**, crea l'ambiente e installa le dipendenze lanciando lo script di setup automatico bash fornito:

   ```bash
   ./setup_env.sh
   ```

4. Per ogni sessione successiva, attiva direttamente l'ambiente ed esegui:

   ```bash
   source venv/bin/activate
   python export_laws_2.py       # Download leggi da Normattiva (JSON)
   python scraping_data.py       # Scraping Agenzia delle Entrate (PDF)
   ```

> **Requisito per `scraping_data.py`:** Google Chrome deve essere installato sul sistema. Lo script scarica automaticamente il ChromeDriver compatibile tramite `webdriver-manager`.

### 3. Nota Specifica: MacBook Air M1 (8GB RAM)

**Avvertenze per MacBook Air M1 (8GB):**

- **`export_laws_2.py` (Normattiva):** Consumo di memoria quasi trascurabile (poche decine di MB). Sfrutta `io.BytesIO()` per decodificare gli archivi al volo senza saturare gli 8GB. Puoi tenerlo in esecuzione in background senza rallentamenti.

- **`scraping_data.py` (Agenzia delle Entrate):** Usa Chrome in modalità headless, che consuma circa 100-200 MB di RAM aggiuntivi. Comunque gestibile sugli 8GB. L'operazione è prevalentemente I/O-bound (rete), quindi il processore riposa costantemente tra le pause.

- **Thermal Throttling & Network:** L'assenza di ventole dell'Air M1 non è un problema per nessuno dei due script. Il colloquio con i server prevede pause fisiologiche per cui il processore non si scalda.

- **Come procedere:** Puoi tranquillamente tenere gli script in esecuzione in background sul terminale mentre continui a lavorare col tuo Mac.

### 4. Installazione Specifica per Raspberry Pi (ARM) e Acer Veriton gn100

Se esegui gli script su un Raspberry Pi o su un Acer Veriton (architettura ARM):

1. **Installazione dipendenze di sistema**: L'architettura ARM richiede l'installazione manuale del browser Chromium e del relativo driver (necessari per lo scraper dell'Agenzia delle Entrate):
   ```bash
   sudo apt-get update
   sudo apt-get install chromium-browser chromium-chromedriver
   ```
   *(Lo script `scraping_data.py` è stato programmato per accorgersi automaticamente di trovarsi su architettura ARM e usare queste versioni di sistema anziché cercare di scaricare Chrome da internet. Gestisce in automatico anche i percorsi delle installazioni via Snap).*

2. **Setup dell'ambiente Python (SOLO LA PRIMA VOLTA)**:
   Crea l'ambiente virtuale e installa le librerie necessarie:
   ```bash
   cd step1_download_laws
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Avvio degli script (Routine per ogni nuovo terminale)**: 
   Ogni volta che apri un nuovo terminale per lavorare al progetto, assicurati di essere nella cartella e attiva l'ambiente:
   ```bash
   cd step1_download_laws
   source venv/bin/activate
   ```
   Se vuoi semplicemente eseguire gli script vedendo l'output a schermo nel tuo terminale, usa questi comandi:
   ```bash
   python3 export_laws_2.py       # Download leggi da Normattiva
   python3 scraping_data.py       # Scraping Agenzia delle Entrate
   ```

4. **Avvio degli script in background (24/7)** (Opzionale): 
   Se invece vuoi che gli script continuino a girare in background anche dopo aver chiuso il terminale (o la connessione SSH), utilizza il comando `nohup`:
   
   Per lo script di Normattiva:
   ```bash
   nohup python3 -u export_laws_2.py > nohup_export_laws.out 2>&1 &
   ```
   
   Per lo script dell'Agenzia delle Entrate:
   ```bash
   nohup python3 -u scraping_data.py > nohup_scraping.out 2>&1 &
   ```

   Per controllare lo stato di avanzamento in tempo reale, usa il comando `tail -f`:
   ```bash
   tail -f nohup_export_laws.out
   # oppure
   tail -f nohup_scraping.out
   ```

Quando hai finito, se desideri uscire dall'ambiente virtuale su terminale, ti basta digitare il comando `deactivate`.
