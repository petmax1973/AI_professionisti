# Obiettivo dello Step 1: Acquisizione dei Dati Legali (Download)

Lo script

step1_download_laws/export_laws_2.py
 è il motore di acquisizione (crawler/downloader) del progetto. Il suo scopo esclusivo è interfacciarsi con le API pubbliche della banca dati statale "Normattiva", interrogare il sistema per trovare le leggi aggiornate e scaricarle in un formato strutturato (JSON) per la successiva elaborazione.

A differenza di uno scaricamento manuale, questo script automatizza la complessa "danza" asincrona richiesta dal server ministeriale per generare l'esportazione di una legge.

Come funziona lo script passo per passo:

1. Configurazione Parametrica Iniziale All'inizio del file sono definite delle costanti cruciali:

EFFECTIVE_DATE / START_DATE_OF_ENACTMENT: I filtri temporali per restringere il campo di ricerca.
MAX_DOCS_PER_TYPE: Limita il numero di documenti da scaricare per ogni tipologia (utile per test veloci o per scaricare solo le ultimissime novità). Se impostato su `None`, lo script attiverà la "Paginazione Automatica" e scaricherà TUTTI i documenti disponibili andando indietro nel tempo fino alla data di `START_DATE_OF_ENACTMENT`.
ACT_TYPES: Una lista esaustiva di 30 tipologie di atti (Costituzione, Leggi, Decreti Legislativi, DPCM, ecc.) che l'IA dovrà conoscere.
2. Ricerca e Filtraggio Iniziale Per ognuno dei 30 tipi di atto legislativo definiti, lo script interroga l'API di "Ricerca Avanzata" (ricerca/avanzata). Richiede al server l'elenco dei documenti più recenti (fino a MAX_DOCS_PER_TYPE) e recupera una prima lista di metadati basilari (Titolo, Numero, Anno).

1. Verifica di Esistenza (Idempotenza) Prima di avviare il pesante processo di download, lo script costruisce il nome del file finale (es. legge_27_february_2026_n_26.json) traducendo i mesi in inglese standard per coerenza internazionale. Se questo file è già presente sul disco (nella sua sotto-cartella specifica), lo script lo "salta" in modo intelligente. Questo significa che puoi eseguire lo script tutti i giorni, e scaricherà solo le nuove leggi emanate in quelle ultime 24 ore, risparmiando tempo e connettività.

2. Il Ciclo di Esportazione Asincrona (La "Danza" API) Se il file è una novità, lo script inizia la comunicazione con Normattiva. Il download non è immediato, ma richiede 4 passaggi di rete obbligatori:

Richiesta di Estrazione: Invia un payload specificando l'atto esatto, chiedendo al server di preparare un'esportazione in formato "JSON". Riceve indietro un "Token" di tracciamento.
Conferma: Invia una seconda chiamata per "confermare" l'avvio del lavoro.
Polling (Attesa Attiva): Il server ministeriale impiega del tempo per generare il pacchetto. Lo script "bussa" periodicamente (ogni 4 secondi) a un endpoint di stato (check-status) finché il server non risponde che il pacchetto è pronto (stato "3").
Download Reale: Solo a questo punto avvia lo scaricamento vero e proprio dei dati.
5. Estrazione Ottimizzata In-Memory (Zero IO Access) Il server del ministero restituisce sempre il file compresso dentro un archivio .zip. Invece di salvare il .zip sull'hard disk, decomprimerlo, leggere il file e poi cancellare i file temporanei, lo script utilizza l'ottimizzazione io.BytesIO().

Scarica l'intero archivio .zip direttamente nella memoria RAM del Mac.
Lo "scompatta" elettronicamente al volo in mezzo decimo di secondo.
Estrae il puro file JSON da dentro l'archivio volatile.
Salva direttamente quel prezioso JSON testuale pulito nel percorso finale (es. documents_collection/legge/).
In sintesi per la documentazione: Lo script è un worker autonomo e resiliente. Interroga le API Statali, controlla se ci sono leggi nuove che non possiedi ancora rispetto al tuo archivio locale, gestisce l'intero ciclo asincrono di creazione del pacchetto sui server ministeriali, decodifica gli archivi compatti in RAM e deposita documenti legali in rigorosi file JSON divisi per categoria. Costituisce la sorgente dati affidabile e pulsante di tutto il sistema RAG.

---

Come Eseguire lo Script `export_laws_2.py` (Requisiti e Installazione):

Questo script richiede un ambiente virtuale isolato (`venv`) per gestire la dipendenza esterna `requests`. Di seguito le istruzioni divise per tipologia di hardware.

## 1. Installazione Generale (Linux / Windows / Cloud)

Per eseguire lo script di acquisizione dati su un server cloud generico, una VPS Linux o un PC Windows:

1. Apri un terminale o prompt dei comandi.
2. Posizionati all'interno della cartella dello Step 1 (`cd step1_download_laws`).
3. Crea e attiva l'ambiente, poi installa le dipendenze:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # (Su Windows: venv\Scripts\activate)
   pip install -r requirements.txt
   ```

4. Esegui lo script:

   ```bash
   python export_laws_2.py
   ```

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
   python export_laws_2.py
   ```

### 3. Nota Specifica: MacBook Air M1 (8GB RAM)

**Avvertenze per MacBook Air M1 (8GB):**
Trattandosi di uno script Python orientato prevalentemente all'I/O di rete (download da API) e non al Machine Learning intensivo, le dipendenze (`requests`) sono estremamente leggere.

* **RAM:** Il consumo di memoria di questo script è quasi trascurabile (poche decine di MB in RAM). Sfruttando l'oggettistica in-memory (`io.BytesIO()`), gli archivi piccoli vengono decodificati "al volo" al netto della RAM unificata, senza saturare gli 8GB. Non è necessario chiudere le altre app per eseguire questa operazione.
* **Thermal Throttling & Network:** L'assenza di ventole dell'Air M1 non è un problema per questo specifico Step. Il colloquio con i server Normattiva prevede pause fisiologiche asincrone (polling onestamente atteso in rete) per cui il processore riposa costantemente. L'operazione "pesante" non è il calcolo, ma l'attesa.
* **Come procedere:** Puoi tranquillamente tenere lo script in esecuzione in background sul terminale tramite il normale comando macOS (vedi sopra: `source venv/bin/activate` + `python export_laws_2.py`) mentre continui a lavorare col tuo Mac senza avvertire rallentamenti di sistema.

Quando hai finito, se desideri uscire dall'ambiente virtuale su terminale, ti basta digitare il comando `deactivate`.
