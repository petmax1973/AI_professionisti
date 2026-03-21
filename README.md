# AI Professionisti

Un ecosistema di Intelligenza Artificiale locale e verticale, progettato specificamente per professionisti (commercialisti, avvocati, medici, amministratori di condominio) per l'elaborazione di grandi moli di dati sensibili in **totale privacy**.

A differenza delle soluzioni in cloud (es. ChatGPT), questo sistema opera interamente **offline** su hardware locale. Questo garantisce la totale conformità al GDPR e la protezione assoluta del segreto professionale.

Il progetto si basa su una strategia ibrida:

* **Fine-Tuning** per far acquisire all'IA il linguaggio tecnico, il ragionamento e il tono del settore.
* **RAG (Retrieval-Augmented Generation)** per la consultazione dinamica di leggi, circolari, e fascicoli/documenti privati dei clienti.

---

## Architettura del Progetto e Passaggi (Steps)

Il progetto è strutturato in una pipeline modulare composta da vari step, ognuno contenuto in una directory dedicata:

### [step1_download_laws](./step1_download_laws/)

**Acquisizione Dati (Harvesting)**
Download di testi normativi, circolari e documenti da fonti ufficiali (es. API Normattiva, Agenzia delle Entrate) tramite script e automazioni, ottenendo documenti strutturati ed evitando lo scraping dove possibile.

### [step2_preprocessing](./step2_preprocessing/)

**Preparazione e Chunking (Preprocessing)**
Pulizia dei testi scaricati (rimozione tag XML/HTML, boilerplate) e suddivisione in blocchi semantici (*Recursive Chunking*) con una determinata sovrapposizione (*overlap*) per mantenere il contesto. Preparazione dei metadati.

### [step3_ingestion](./step3_ingestion/)

**Archiviazione nel Vector DB (Ingestion)**
Estrazione del testo, trasformazione nei relativi vettori matematici tramite modelli di embedding locali (es. `nomic-embed-text` o `bge-m3`) e archiviazione all'interno di un Database Vettoriale locale (es. Qdrant o ChromaDB) per consentire la ricerca semantica.

### [step4_inference](./step4_inference/)

**Motore RAG e Inferenza (Inference)**
Sistema di retrieval semantico. Trasforma la query dell'utente in un vettore, effettua la ricerca di similarità nel Vector DB per recuperare il contesto normativo o documentale pertinente, e lo passa al Large Language Model (LLM) locale per generare la risposta accurata.

### [step5_graphical_inference](./step5_graphical_inference/)

**Interfaccia Utente (Deployment & UI)**
Applicazione desktop/frontend reattiva per il professionista. Fornisce un'interfaccia di chat intuitiva e permette il caricamento (drag & drop) di documenti locali dei clienti (RAG "on-demand") elaborando i dati in tempo reale senza mai uscire dal PC locale.

### [step6_finetuning](./step6_finetuning/)

**Creazione Dataset e Fine-Tuning**
Generazione di dataset (domande/risposte tecniche a partire dai testi normativi) e addestramento del modello locale (*QLoRA* su modelli come Llama 3 o Qwen) per insegnare logica e terminologia specifica, creando così un "esperto" di dominio (es. Modello-Commercialista, Modello-Penalista).

### [documentazione](./documentazione/)

**Documentazione Tecnica e Guide**
Guide di progetto, documentazione API (es. Normattiva), strategie hardware e budget, e riassunti sullo sviluppo e le procedure in ambito AI per professionisti.
