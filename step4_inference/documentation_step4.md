Obiettivo dello Step 4: Interrogazione e Generazione (RAG Inference)
Lo script `step4_inference/chat_rag.py` rappresenta l'interfaccia utente finale del sistema AI. Il suo scopo è permettere a un commercialista di dialogare in linguaggio naturale con l'intera banca dati legislativa creata nello Step 3.

Come funziona lo script passo per passo:

1. Inizializzazione della Memoria (ChromaDB)
All'avvio, lo script si collega al database vettoriale `laws_vector_db` costruito precedentemente. Re-inizializza il modello matematico (`intfloat/multilingual-e5-base` ottimizzato per Apple Silicon via `mps`) in modalità "sola lettura", pronto a tradurre le tue domande in vettori.

2. Inizializzazione del "Cervello" (Ollama LLM)
Lo script si connette al server locale Ollama in esecuzione in background sul tuo Mac, agganciando il modello di linguaggio `llama3`. Usare un modello in locale (invece di ChatGPT via API) garantisce che nessuna richiesta o dato sensibile esca mai dal tuo computer: privacy assoluta al 100%.

3. L'Inquadramento Fotografico (Il Prompt)
Il cuore dell'intelligenza è il "Prompt Template". Abbiamo impartito a Llama3 tre direttive di ferro:
- Regola 1: Non usare alcuna conoscenza esterna al contesto fornito. Non inventare leggi.
- Regola 2: Se la risposta non c'è, ammettilo.
- Regola 3: Cita sempre le fonti esatte lette dal database.
Queste barriere trasformano un'intelligenza artificiale generica in un assistente legale severo e preciso.

4. Il Loop di Ricerca (Retrieval-Augmented Generation)
Ogni volta che fai una domanda nel terminale, avviene questa magia:
- La tua frase viene vettorializzata.
- Il sistema recupera i 4 frammenti di legge (chunks) matematicamente più vicini al significato della tua domanda (spesso in una frazione di secondo).
- Lo script impacchetta invisibilmente quei 4 articoli di legge assieme alla tua domanda e alle regole di ferro, passandoli a Llama 3 come un unico testo da elaborare.
- Llama 3 legge i "documenti sulla scrivania", pensa alla risposta e la scrive a schermo.
- Alla fine, lo script ti stampa in chiaro l'elenco esatto degli articoli (Source ID) che Llama ha letto per elaborare quella risposta.

In sintesi per la documentazione:
Lo script `chat_rag.py` chiude il cerchio del progetto. Unisce in tempo reale il motore di ricerca semantico (Retrieval) con la capacità espositiva di un LLM (Augmented Generation). Ti fornisce una chat infinita per studiare le leggi senza mai far uscire un bit di informazione dal tuo Mac.


# ==========================================
# STEP 4: REQUISITI E ISTRUZIONI PER L'AVVIO
# ==========================================

0. **Prerequisito Universale**: Assicurati che l'applicazione **Ollama** sia installata, avviata e in esecuzione in background sulla tua macchina. Assicurati anche di aver scaricato il modello di base aprendo un terminale e digitando `ollama run llama3.2` o un modello equivalente.

Questo step interroga il Vector DB creato in precedenza. Anche qui usiamo `langchain` e `sentence-transformers`, quindi l'ambiente virtuale è obbligatorio.

### 1. Installazione Generale (Linux / Windows / Cloud)
Per avviare la chat su macchine standard:

1. Apri un terminale.
2. Posizionati all'interno della cartella dello Step 4:

   ```bash
   cd step4_inference
   ```

3. Crea e attiva l'ambiente:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # (Oppure venv\Scripts\activate su Windows)
   pip install -r requirements.txt
   ```

4. Esegui lo script della chat:

   ```bash
   python3 chat_rag.py
   ```

### 2. Installazione Specifica per Sistemi macOS
Per l'utilizzo su sistemi Mac con chip Intel o Apple Silicon:

1. Apri il Terminale.
2. Posizionati all'interno della cartella temporale:

   ```bash
   cd step4_inference
   ```

3. **Solo ed esclusivamente la prima volta**, installa l'ambiente con lo script bash:

   ```bash
   ./setup_env.sh
   ```

4. Per ogni sessione successiva, attiva l'ambiente ed esegui la chat:

   ```bash
   source venv/bin/activate
   python3 chat_rag.py
   ```

### 3. Nota Specifica: MacBook Air M1 (8GB RAM)
⚠️ **Avvertenze sulle prestazioni in Chat per Mac M1 (8GB):** 
Questo è il momento in cui l'efficienza è tutto, poiché farai domande e pretenderai risposte in tempi ragionevoli da un computer senza dissipazione attiva e con una memoria limitata.

* **Sforzo Combinato (Modello Vettorio + LLM Insieme):** Quando avvii la chat, si attivano due intelligenze artificiali *simultaneamente* nella tua RAM da 8GB. 
  1. Il piccolissimo modello `intfloat/multilingual-e5-base` (in Python) per interpretare la tua domanda.
  2. L'enorme modello Llama3 (dentro Ollama) per generare la risposta logica basata sulle leggi trovate per te. 
  L'occupazione di RAM sarà vicina al limite o la supererà (Swap in azione). **Mai come ora è vitale chiudere assolutamente ogni altra applicazione** (browser, slack, mail) per lasciare l'hardware vitale alla memoria.
* **Thermal Throttling Dinamico:** Rispetto allo step 3, in chat farai una domanda, il Mac scriverà la risposta per 10-20 secondi scaldandosi, ma poi *aspetterà* la tua domanda successiva raffreddandosi. Questo ciclo "Start and Stop" è ideale per il design passivo dell'Air M1, che non subirà drastici tagli di potenza rispetto all'uso intensivo continuo.
* **Vantaggio dell'Architettura M1:** Lo script è configurato per usare i Metal Performance Shaders (`device="mps"`). Il retrieval (il recupero dei PDF) avverrà in millisecondi sulla GPU. Il vero "lavoro pesante" sarà la scrittura della risposta di Llama in stretta collaborazione intelligente con Ollama. Sarai sorpreso della velocità nativa.

Quando hai finito la sessione di chat, premi `Ctrl+C` per terminare lo script e poi digita `deactivate` per uscire.

# ==========================================
# DIPENDENZE (requirements.txt)
# ==========================================
langchain==0.2.14
langchain-community==0.2.12
langchain-huggingface==0.0.3
chromadb==0.5.5
sentence-transformers==3.0.1
pydantic==2.8.2