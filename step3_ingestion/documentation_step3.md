# Obiettivo dello Step 3: Indicizzazione e Vettorializzazione (Ingestion)

Lo script `step3_ingestion/ingest_rag.py` rappresenta la fase finale della preparazione dei dati. Il suo scopo è prendere i frammenti di testo "leggibili dall'uomo" (creati nello Step 2) e tradurli in un formato matematico "leggibile dall'Intelligenza Artificiale", salvandoli in un database vettoriale interrogabile.

Come funziona lo script passo per passo:

1. Inizializzazione del Modello linguistico (Embedding)
Il cuore dello script è il modello di "embedding". Lo script scarica e inizializza un modello linguistico open-source specializzato (`intfloat/multilingual-e5-base`), ottimo per la lingua italiana e il linguaggio legale.
Questo modello non "legge" le parole, ma le trasforma in vettori semantici (lunghe sequenze di numeri) che ne catturano il reale significato profondo.
Inoltre, per garantire massime prestazioni, lo script tenta di sfruttare l'accelerazione hardware della scheda video (`mps` sui chip Apple Silicon M1/M2/M3 o `cuda` su macchine NVIDIA), ripiegando sulla normale CPU (`cpu`) se non disponibile.

2. Lettura del Dataset in Streaming
Lo script deve elaborare tutti i dataset JSONL generati nello Step 2, contenuti nella cartella `accountant_rag_dataset/` (ad esempio `dataset_rag_langchain.jsonl` per le leggi Normattiva e `dataset_agenzia_langchain.jsonl` per i documenti dell'Agenzia delle Entrate). Lo script scopre automaticamente tutti i file `.jsonl` presenti nella cartella tramite `glob`, concatenandoli in un unico flusso di documenti. Invece di caricare l'intero file in memoria RAM (che potrebbe causare blocchi se il file è enorme), utilizza un "Generatore Python" (tramite la funzione `iter_jsonl_documents` e `combined_document_iterator`).
Questo approccio permette di leggere i dataset riga per riga costantemente: carica un singolo chunk, estrae il testo e i metadati, lo passa alla fase successiva per la catalogazione ed elimina quello in memoria per fare spazio al successivo. Inoltre, aggiungere nuove fonti di dati in futuro è automatico: basta generare un nuovo file `.jsonl` nella stessa cartella.

3. Vettorializzazione a Blocchi (Batching)
Una volta letto un frammento, il modello di embedding lo converte in coordinate matematiche. Poiché questa operazione richiede molta potenza di calcolo, lo script organizza il lavoro a blocchi (batch) di 100 documenti alla volta.
Invia questi 100 documenti al modello, ottiene le traduzioni matematiche e le accumula. Questo approccio a lotti assicura estrema velocità e previene surriscaldamenti anomali.

4. Creazione e Salvataggio del Database Vettoriale (ChromaDB)
Man mano che i blocchi vengono vettorializzati, vengono immediatamente salvati in un database vettoriale locale chiamato `ChromaDB`.
Il database viene fisicamente creato o aggiornato per persistere nel tempo all'interno della cartella `laws_vector_db`.
Questo database non archivia semplicemente i testi, ma li mappa graficamente in uno spazio tridimensionale infinito in base al loro "significato geometrico". In futuro, quando un utente farà una domanda al RAG, il sistema trasformerà la domanda in un vettore e cercherà nel database i paragrafi di legge che sono posti "più vicini" al significato della domanda.

In sintesi per la documentazione:
Lo script `ingest_rag.py` agisce come un traduttore matematico e un archivista. Prende il testo legale pulito, lo analizza semanticamente tramite un modello di intelligenza artificiale locale e popola in streaming un database vettoriale (ChromaDB) lavorando in blocchi ottimizzati. Il risultato finale è un motore di ricerca locale incancellabile, pronto per essere interrogato istantaneamente da un LLM per generare risposte legali ultra-precise.

<!-- ========================================== -->

## STEP 3: REQUISITI E ISTRUZIONI PER L'INGESTION

<!-- ========================================== -->

Questo step prende i frammenti di testo elaborati dallo Step 2 e li converte in un Database Vettoriale tramite ChromaDB e HuggingFace Embeddings (`sentence-transformers`). Questo calcolo è molto intensivo e richiede un ambiente isolato (`venv`). La primissima volta esegue un download del modello `intfloat/multilingual-e5-base` (~500MB).

### 1. Installazione Generale (Linux / Windows / Cloud)

Per l'uso su macchine Windows PC, server Linux o macchine Cloud (meglio se munite di schede video NVIDIA):

1. Apri un terminale.
2. Posizionati nella cartella dello Step 3:

   ```bash
   cd step3_ingestion
   ```

3. Crea un ambiente virtuale e installa le librerie:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # (Oppure venv\Scripts\activate su Windows)
   pip install -r requirements.txt
   ```

4. Solo se si ha una GPU NVIDIA, installare Torch per CUDA (opzionale ma raccomandato per la massima velocità).
5. Lancia l'indicizzazione:

   ```bash
   python3 ingest_rag.py
   ```

### 2. Installazione Specifica per Sistemi macOS

Per l'utilizzo su sistemi Mac recenti con chip Apple Silicon (M1, M2, ecc.), sfrutteremo l'accelerazione neurale Apple `MPS` direttamente integrata nelle librerie.

1. Apri il Terminale di macOS.
2. Vai nella cartella:

   ```bash
   cd step3_ingestion
   ```

3. **Solo ed esclusivamente la prima volta**, crea l'ambiente e installa in blocco le pesanti dipendenze lanciando lo script bash fornito:

   ```bash
   ./setup_env.sh
   ```

4. Per ogni sessione successiva, attiva direttamente l'ambiente ed esegui:

   ```bash
   source venv/bin/activate
   python3 ingest_rag.py
   ```

### 3. Nota Specifica: MacBook Air M1 (8GB RAM)

**Avvertenze per Mac con 8GB di RAM:** Questo è il primo passaggio che **stressa contemporaneamente sia la CPU/GPU che la memoria** del tuo MacBook Air.

* **La gestione della RAM (8GB):** Il modello linguistico richiesto occupa circa 500MB, Langchain e ChromaDB ne richiedono altre centinaia per avviarsi. In aggiunta, i batch di 100 documenti JSON alla volta occupano ulteriore spazio transitorio in memoria. Questo causerà inevitabilmente l'uso marginale della memoria di Swap (disco SSD) se hai altre cose aperte. **È fondamentale chiudere i browser web e i software pesanti prima di lanciare lo script**.
* **Accelerazione MPS Integrata:** Lo script Python interno è già pre-configurato per identificare automaticamente il tuo processore M1 e attivare il modulo `device="mps"` (Metal Performance Shaders) di PyTorch. Questo scarica il faticosissimo calcolo vettoriale sui core grafici della GPU integrata nell'M1, salvando il processore principale.
* **Thermal Throttling (Occhio al calore):** Usare ininterrottamente la GPU MPS per tradurre migliaia di articoli genererà calore. Siccome l'Air M1 disperde passivamente senza ventole, dopo circa 5-10 minuti di esecuzione continuata potresti percepire la scocca molto calda. È un comportamento normale e il Mac ridurrà autonomamente la frequenza (*Thermal Throttling*) proteggendo l'hardware, pur continuando fedelmente e un po' più lentamente a convertire i testi.
* **Conclusione del RAG:** Il processo è asincrono a lotti: puoi interromperlo con Ctrl+C qualora notassi rallentamenti spropositati; gli elementi già elaborati e depositati in ChromaDB non andranno persi.

Quando hai finito con lo Step 3, puoi uscire dall'ambiente virtuale digitando:
`deactivate`

<!-- ========================================== -->

## DIPENDENZE (requirements.txt)

<!-- ========================================== -->

langchain==0.2.14
langchain-community==0.2.12
langchain-huggingface==0.0.3
chromadb==0.5.5
sentence-transformers==3.0.1
pydantic==2.8.2
