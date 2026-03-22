# Obiettivo dello Step 2: Preprocessing per il RAG

Lo script

step2_preprocessing/preprocess_rag.py
 ha un compito fondamentale: fare da ponte tra i dati "grezzi" scaricati dal governo e il cervello dell'intelligenza artificiale.

I file JSON scaricati dall'API di Normattiva sono alberi molto complessi e annidati, pensati per i database ministeriali, ma inutilizzabili così come sono da un LLM (Large Language Model). Questo script "appiattisce", pulisce e arricchisce i dati, convertendoli in "chunks" (frammenti) ideali per la ricerca vettoriale.

Come funziona lo script passo per passo:

1. Scansione delle cartelle (Streaming Reale) Lo script non carica tutto in memoria. Utilizza una ricerca ricorsiva (glob.glob(..., recursive=True)) per trovare tutti i file .json scaricati, anche se divisi in sottocartelle (es. COSTITUZIONE, LEGGE, ecc.). Elabora un file per volta, garantendo che il consumo di memoria RAM resti bassissimo anche se si elaborano decine di migliaia di leggi.

2. Estrazione dei Metadati Globali Per ogni legge, lo script legge la "testata" (funzione extract_law_metadata).

Recupera informazioni cruciali come:

- Tipo di atto (es. "Decreto Legge")
- Numero e Anno
- Data di emanazione
- Titolo completo
- URN (Identificativo univoco)

Perché lo fa? Perché un singolo articolo di legge, estratto dal suo contesto, non ha senso. Lo script si "imprime" questa carta d'identità della legge per poterla poi "incollare" su ogni singolo articolo o comma estratto successivamente.

1. Navigazione Ricorsiva nel cuore della Legge Le leggi ministeriali hanno strutture imprevedibili: Testo -> Titolo -> Capo -> Articolo -> Comma. La funzione

extract_articles_recursive
 naviga intelligentemente questo labirinto. Scende nell'alberatura del JSON finché non trova i due elementi di maggiore interesse per un commercialista:

Gli Articoli (il corpo della legge)
Gli Allegati (dove molto spesso si nascondono tabelle, aliquote o specifiche tecniche cruciali).
4. Arricchimento Semantico (Chunking Intelligente) Quando trova un articolo, lo script non si limita a copiare il testo, ma costruisce un frammento di testo ("chunk") altamente ottimizzato per l'Intelligenza Artificiale. Costruisce un testo formattato che include letteralmente:

Il titolo ("Rubrica") dell'articolo.
Il corpo del testo pulito dai caratteri sporchi.
Le Note Esplicative, se presenti (spesso essenziali per l'interpretazione).
Una testata testuale generata dinamicamente (es. "Reference: LEGGE number 27 of the 2026-02-27..." e "Validity starting from: 2026-02-28").
Perché questa iniezione di testo è fondamentale? Perché quando l'IA leggerà questo frammento in futuro per rispondere a una domanda, avrà direttamente all'interno dello stesso paragrafo sia la regola, sia la validità temporale, sia a quale legge appartiene, migliorando drasticamente la precisione delle risposte (RAG).

1. Creazione del Dataset Scalabile (JSONL) Invece di creare un nuovo gigantesco file JSON, lo script salva il risultato nel formato JSONL (JSON Lines) nel file accountant_rag_dataset/dataset_rag_langchain.jsonl. In questo formato, ogni singola riga del file di testo rappresenta un intero e valido oggetto JSON indipendente. Questo è il formato standard industriale (usato da OpenAI, Langchain, ecc.) per addestrare o alimentare AI su terabytes di dati, perché permette allo "Step 3 (Ingestion)" di leggere il dataset riga per riga senza saturare la RAM.

 In sintesi per la documentazione: Lo script trasforma complessi alberi istituzionali in frammenti di conoscenza piatti e indipendenti. Ogni frammento (chunk) creato contiene il testo completo di un singolo articolo o allegato, arricchito con la data di validità, le note esplicative e le etichette per risalire alla legge padre, salvando il tutto in un formato streaming "JSONL" pronto per l'indicizzazione vettoriale.

---

## Script 2: `preprocess_agenzia.py` — Preprocessing Documenti Agenzia delle Entrate

Lo script `preprocess_agenzia.py` è il complemento di `preprocess_rag.py`. Mentre quest'ultimo elabora i file JSON strutturati scaricati dall'API di Normattiva, `preprocess_agenzia.py` si occupa dei documenti **non strutturati** (PDF) scaricati dal sito dell'Agenzia delle Entrate dallo script `scraping_data.py` dello Step 1.

### Come funziona lo script passo per passo

1. **Scansione ricorsiva dei PDF** — Lo script cerca ricorsivamente tutti i file `.pdf` e `.PDF` nella cartella `step1_download_laws/archivio_agenzia_entrate/`, elaborandoli uno alla volta in streaming per mantenere basso il consumo di RAM.

2. **Estrazione testo con PyMuPDF** — Utilizza la libreria `PyMuPDF` (`fitz`) per estrarre il testo grezzo pagina per pagina da ciascun PDF. I documenti gestiti includono Circolari, Provvedimenti, Risoluzioni e Risposte agli Interpelli.

3. **Sanitizzazione del testo** — I PDF dell'Agenzia delle Entrate contengono spesso caratteri di controllo (form-feed, NUL, vertical-tab) ereditati dalla digitalizzazione. La funzione `sanitize_text()` li rimuove automaticamente, garantendo che il JSON generato sia sempre valido.

4. **Chunking semantico** — A differenza dei JSON di Normattiva (che hanno una struttura naturale ad "articoli"), i PDF sono testi lunghi e continui. Lo script utilizza il `RecursiveCharacterTextSplitter` di LangChain per suddividerli in frammenti di **1500 caratteri** con una sovrapposizione (**overlap**) di **150 caratteri**, evitando che concetti vengano troncati a metà frase.

5. **Estrazione metadati dal nome file** — Poiché i PDF non contengono metadati strutturati, lo script ricostruisce tipo di atto, numero e anno tramite analisi Regex del nome del file (es. `Circolare+n+7+del+9+aprile+2019_Circolare+N.+7_09042019.pdf`).

6. **Arricchimento dei chunk** — Come fa `preprocess_rag.py`, ogni frammento viene arricchito con una testata testuale che inietta i metadati direttamente nel `page_content` (es. `"Reference: Circolare N. 7 del 2019"`), migliorando la precisione delle risposte del RAG.

7. **Output JSONL** — Il risultato viene salvato in `accountant_rag_dataset/dataset_agenzia_langchain.jsonl`, con lo **stesso identico schema** (`metadata` + `page_content`) utilizzato da `preprocess_rag.py`. Questo garantisce piena compatibilità con lo Step 3 (Ingestion).

### Dipendenze

Questo script richiede due librerie aggiuntive, da installare nel venv dello Step 3:

```bash
pip install PyMuPDF langchain-text-splitters
```

### Output

```text
step2_preprocessing/accountant_rag_dataset/
├── dataset_rag_langchain.jsonl       ← Leggi da Normattiva (Step 2 originale)
└── dataset_agenzia_langchain.jsonl   ← Documenti Agenzia delle Entrate (nuovo)
```

---

Come Eseguire lo Script `preprocess_rag.py` (Requisiti e Installazione):

Questo script utilizza esclusivamente le librerie standard di Python (`json`, `os`, `glob`), quindi non richiede l'installazione di librerie esterne tramite `pip`. È un processo "puro" e nativo.

## 1. Installazione Generale (Linux / Windows / Cloud)

Su un server o un PC generico, è sufficiente avere Python 3 installato.

1. Apri un terminale.
2. Posizionati all'interno della cartella dello Step 2:

   ```bash
   cd step2_preprocessing
   ```

3. Esegui lo script direttamente con Python:

   ```bash
   python3 preprocess_rag.py
   ```

## 2. Installazione Specifica per Sistemi macOS

I moderni sistemi Mac non includono più Python di default tra gli eseguibili di sistema base, ma solitamente è installato tramite Homebrew o Developer Tools.

1. Apri l'app Terminale.
2. Posizionati all'interno della cartella:

   ```bash
   cd step2_preprocessing
   ```

3. Assicurati di non avere attivi altri `venv` e avvia lo script standard:

   ```bash
   python3 preprocess_rag.py
   ```

## 3. Nota Specifica: MacBook Air M1 (8GB RAM)

**Avvertenze per MacBook Air M1 (8GB):**
Lo script di preprocessing è stato progettato esplicitamente per aggirare i limiti di memoria fisica.

- **RAM limitata:** L'operazione `glob` utilizzata dal codice non carica mai nell'array in memoria l'intero contenuto dei file JSON. Apre un file, lo formatta, e "vomita" (appende) la riga convertita nel file `dataset_rag_langchain.jsonl`, per poi distruggere l'oggetto testuale dalla memoria e passare al successivo. Grazie a questo design in streaming iterativo, l'impatto sugli 8GB di RAM del tuo M1 è virtualmente inesistente. Non provocherà memory swap intensivo.
- **CPU:** Il chip M1 è brillantemente veloce nelle operazioni di parse testuale. Rispetto a una CPU tradizionale, terminerà questo lavoro con estrema rapidità.
- **Thermal Throttling:** Non ci saranno problemi di surriscaldamento poiché l'operazione durerà una manciata di secondi, ben al di sotto della soglia necessaria per scaldare il telaio in alluminio dell'Air.
- **Esecuzione sicura:** Puoi lanciare l'astrazione JSONL senza alcun accorgimento particolare ("`python3 preprocess_rag.py`") anche con altri programmi attivi.
