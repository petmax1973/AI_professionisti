# Guida Educativa: Sistemi AI Locali su MacBook Air M1

## Un percorso di studio per comprendere l'ecosistema AI offline

### Descrizione Generale del Progetto

L'obiettivo di questo documento è puramente **educativo e di studio**. Esploreremo come realizzare, a livello concettuale e sperimentale, un ecosistema AI verticale direttamente su un **MacBook Air M1 (8GB RAM, 512GB SSD)**.

A differenza dello scenario professionale o di produzione, lo scopo non è l'uso su dati reali di clienti per la conformità GDPR, bensì comprendere le meccaniche di base del Machine Learning, della Retrieval-Augmented Generation (RAG) e dei severi limiti hardware nell'addestramento (Fine-Tuning) di Large Language Models (LLM) su macchine consumer entry-level. Lavoreremo interamente offline per "aprire la scatola nera" dell'Intelligenza Artificiale.

---

## 🛠 Percorso di Studio in 7 Step

### STEP 1: Conoscere l'Hardware e i suoi Limiti

In questo scenario educativo, il nostro ambiente di sviluppo e di utilizzo coincidono nella stessa macchina.

* **Hardware**: MacBook Air M1 con 8GB di RAM Unificata (Apple Silicon) e 512GB SSD.
* **Le Sfide Architetturali**: La CPU/GPU M1 (Neural Engine) è estremamente efficiente, ma gli **8GB di RAM sono il vero collo di bottiglia**. Le architetture LLM richiedono enormi quantità di memoria (VRAM/RAM) sia per l'addestramento che per l'esecuzione. Su questo Mac, l'SSD verrà usato pesantemente in "Swap" se la RAM si satura, un processo che rallenta l'elaborazione e usura il disco.
* **Sistema Operativo e Framework**: macOS. Le librerie standard del settore NVIDIA (CUDA) non funzionano qui. Utilizzeremo tool multipiattaforma (come `llama.cpp` o **Ollama**) e l'ecosistema **MLX** di Apple (ottimizzato per i chip M) per i test di addestramento.

### STEP 2: Acquisizione Dati Educativi (Sourcing)

Per scopi didattici, non serve scaricare archivi immensi di leggi o referti. Ci basta un piccolo dataset di test ("Toy Dataset").

* **API Pubbliche**: Puoi testare lo scaricamento di open data o testare le API (come Normattiva Open Data) limitandoti a scaricare 1 o 2 file XML per capire il meccanismo di connessione e parsing XML/JSON.
* **Dataset Pronti**: Per l'addestramento e il testing, conviene partire da file `csv` o `jsonl` di piccole dimensioni (es. 100-500 righe) direttamente scaricabili da hub educativi come Hugging Face.
* **Estrazione Testo**: Scarica 2-3 PDF didattici di pubblico dominio e studia le tecniche in Python per estrarne il testo "pulito" tramite librerie come `PyMuPDF` o `pdfplumber`.

### STEP 3: Preparazione e Chunking (Preprocessing)

Per capire come un LLM "legge" lunghi documenti, il testo va frammentato (Chunking).

* **Librerie**: Usa script Python standard (o funzioni di framework come LangChain).
* **Dividere e Sovrapporre**: Dividi i testi in piccoli blocchi (es. 500 caratteri) con una sovrapposizione (**overlap**) di 50-100 caratteri. I blocchi molto piccoli evitano di esaurire la ridotta memoria di contesto (Context Window) dei piccoli LLM che questo hardware può supportare.

### STEP 4: Sintesi del Dataset

Scoprire la struttura formale per "insegnare" a un LLM come rispondere.

* Invece di far generare le coppie Domanda/Risposta a un potentissimo (e inarrivabile per gli 8GB) LLaMA 3 70B, puoi compilare manualmente un micro-dataset `JSONL` di 20 righe.
* Impara l'anatomia della entry: `instruction` (cosa viene chiesto), `input` (il contesto opzionale fornito) e `output` (le risposta desiderata). Anche un dataset di 10 righe è sufficiente per capire l'architettura logica.

### STEP 5: Addestramento sperimentale (Limiti del Fine-Tuning)

**Attenzione: Il Fine-Tuning completo o utile su un M1 con 8GB di RAM è praticamente impossibile; lo faremo solo a scopo accademico per vedere l'algoritmo funzionare.**

* **Modelli Consigliati per studio**: Utilizza modelli "minuscoli", come **Qwen 2.5 0.5B / 1.5B** o **Llama-3.2 1B / 3B**.
* **Il Metodo (Apple MLX)**: Abbandonato Unsloth (basato su NVIDIA CUDA), studieremo l'uso di **MLX** (il framework di Apple) o **MLX-LM** per fare script di un micro fine-tuning usando LoRA (Low-Rank Adaptation) che aggiorna solo una frazione dei parametri.
* **Gestione RAM**: Durante l'esecuzione del codice di training, anche con LoRA a 4-bit, le memorie si scontreranno con gli 8GB massimi (con un rischio elevato di crash "Out of Memory" - OOM). Sarà obbligatorio impostare `batch_size=1` e processi di lunghezza minima. Lo scopo è solo vedere la progress-bar avanzare, non produrre un tool reale.

### STEP 6: Esecuzione del Modello (Ollama)

Questa è la fase che darà le maggiori soddisfazioni sul M1 8GB.

* **Inference Engine**: Installa **Ollama** per macOS. Rende semplicissimo scaricare LLM eseguiti nel terminale.
* **Modelli Quantizzati**: La ram impone dei compromessi. Puoi eseguire fluidamente e con ottimi risultati modelli "intelligenti" come `llama3.2:1b` (peso 1.3GB) o `llama3.2:3b` (peso 2.0GB). Modelli più classici come `llama-3.1-8b` esistono in formati "compressi" matematicamente (**Quantizzati** a Q4, occupando ~4.7GB). Gireranno bene, ma prosciugheranno le risorse lasciando poco spazio al sistema operativo.
* **Esplorazione UI**: Con poche righe di codice Python (usando la libreria `ollama` associata a `Gradio` o `Streamlit`) puoi creare rapidamente una tua applicazione locale funzionante.

---

## 🔒 Focus: Privacy vs Didattica

Mentre nello scenario professionale descritto per studi legali e amministrativi l'IA offline è un obbligo dettato da sanzioni, GDPR e segreto professionale, qui il "tutto locale" ha uno scopo diverso: la **sovranità tecnica e lo studio**.
Scaricare i modelli sul proprio PC ed estrarli (fare inferenza) insegna l'indipendenza dai grandi vendor cloud (come OpenAI). Ti permette di esaminare il funzionamento di un sistema vettoriale dissezionando gli algoritmi riga per riga senza consumare crediti o abbonamenti.

---

## 🔍 Focus Tecnico: La RAG "Di Precisione" (8GB RAM)

Realizzare una Retrieval-Augmented Generation (RAG) su un computer con così poca RAM insegna ad essere programmatori estremamente efficienti:

1. **Embedding Leggero**: È la chiave di volta. Un modello di embedding trasforma i testi in coordinate matematiche. Modelli grandi consumano troppa RAM. Sviluppa usando modelli compatti come `nomic-embed-text` o `all-MiniLM-L6-v2`.
2. **Database Locale Leggero**: Usa un array `NumPy` basilare o **ChromaDB** per salvare questi vettori senza i pesi dei database di tipo Enterprise in Docker (eccessivi per un Air M1).
3. **The Prompt Assembly**: Sperimenta script Python che pescano la frase nel PDF che "matematicamente" somiglia di più alla tua domanda, uniscono frase e domanda in una stringa di testo unica e passano il "pacco" a Ollama per elaborare in fluente linguaggio naturale una risposta didattica.

---

## 📈 Percorso di Studio Programmato: Le Basi AI Locale

Se l'obiettivo è trasformare questo notebook in una vera piattaforma di studio:

* **Mese 1**: Fondamenti di Python e gestione degli ambienti virtuali (`venv`). Interfacciamento con `Ollama` via API Python. Lettura basica di PDF e generazione text-to-text.
* **Mese 2**: Il RAG. Studio delle librerie come `LangChain` per scomporre testo, calcolare embedding con Ollama e salvare vettori con ChromaDB in RAM. Interrogazione di file di testo locali (es. il riassunto di un libro scolastico).
* **Mese 3**: Le tecnologie del limite. Cos'è la quantizzazione (GGUF)? Come fanno ad "amputare" i numeri decimali dei pesi della rete neurale per far entrare giganteschi LLM negli stretti 8GB del Mac, sacrificando una minima percentuale di intelligenza pur di farli funzionare?
* **Mese 4**: Introduzione al framework Apple MLX. Tentativo di creare un adapter LoRA minuscolo per un piccolo modello, monitorando col Task Manager della GPU del Mac come l'AI fagocita la Memoria Unificata. L'arte dell'ottimizzazione estrema.

L'hardware vincolato di questo Mac M1 8GB non è un limite allo studio, bensì un "maestro severo": costringerà chiunque lo usi per fare AI a imparare le fondamenta dell'ottimizzazione del codice e le vere meccaniche interne dell'Intelligenza Artificiale Generativa moderna.
