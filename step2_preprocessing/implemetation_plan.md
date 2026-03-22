Piano di Sviluppo: Integrazione Documenti Agenzia delle Entrate nel RAG
Questo piano descrive i passi necessari per elaborare i documenti non strutturati (PDF, DOC, ecc.) scaricati dal sito dell'Agenzia delle Entrate e integrarli nel database vettoriale, mantenendo un'architettura modulare e scalabile.

User Review Required
Nessuna decisione critica o "breaking change". Viene aggiunta una nuova pipeline di preprocessing in parallelo a quella esistente e si rende più dinamico lo script di ingestion.

Proposed Changes
Step 2: Preprocessing
Creazione di un nuovo script dedicato all'elaborazione dei documenti non strutturati.

[NEW] step2_preprocessing/preprocess_agenzia.py
Questo script avrà le seguenti funzionalità:

Lettura dei file: Scansione ricorsiva della cartella step1_download_laws/archivio_agenzia_entrate per individuare PDF, DOC, DOCX.
Estrazione Testo: Utilizzo di librerie come PyMuPDF (o similari) per estrarre il testo grezzo dai documenti.
Chunking Semantico: Utilizzo di strumenti come RecursiveCharacterTextSplitter di LangChain per dividere i testi lunghi in frammenti (es. 1000-1500 caratteri con overlap).
Metadata Mapping: Estrazione di metadati dal nome del file e dal path (Tipo Atto, Numero, Anno, Data) per allineare la struttura a quella dei documenti Normattiva.
Salvataggio JSONL: Salvataggio dei chunk elaborati nel file step2_preprocessing/accountant_rag_dataset/dataset_agenzia_langchain.jsonl.
Step 3: Ingestion
Modifica dello script di ingestion per supportare file multipli.

[MODIFY] step3_ingestion/ingest_rag.py
Lettura Multipla: Aggiornamento della logica per caricare tutti i file .jsonl presenti nella cartella accountant_rag_dataset/ tramite un loop su glob.glob(), invece di puntare a un singolo file dataset_rag_langchain.jsonl.
Verification Plan
Automated/Manual Tests
Test Preprocessing: Esecuzione di python preprocess_agenzia.py e verifica della corretta creazione del file dataset_agenzia_langchain.jsonl con la struttura corretta di metadata e page_content.
Test Ingestion: Esecuzione di python ingest_rag.py verificando dai log a terminale che il ChromaDB stia ingerendo le righe da entrambi i dataset (Normattiva e Agenzia delle Entrate) senza generare errori di struttura.
