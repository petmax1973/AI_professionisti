Obiettivo dello Step 5: Interfaccia Grafica Chatbot

Lo script `step5_graphical_inference/app.py` fornisce un'interfaccia grafica moderna (stile WhatsApp) per l'interrogazione della banca dati legislativa, sostituendo l'interfaccia da terminale dello Step 4.

L'applicazione utilizza Streamlit per renderizzare nel browser la chat, conservando al contempo le regole di privacy ferree:
1. Nessun dato esce dal Mac.
2. Utilizza il database `laws_vector_db` locale.
3. Utilizza `Ollama` locale per la generazione delle risposte.

L'interfaccia si divide in tre modalità operative, selezionabili dalla barra laterale sinistra (Sidebar):

1. **Ricerca Normativa (Leggi)**: (Predefinita)
   - Interroga le leggi, i codici e le normative di stato contenute nel database vettoriale locale creato nello Step 3.
   
2. **Analisi Documenti Privati**:
   - Permette di caricare dal computer i propri file privati (PDF, CSV, Excel, TXT) come bilanci, visure, o contratti.
   - Crea un "cervello" temporaneo per l'IA valido solo per la sessione corrente. 
   - Premi "Elabora Documenti" dopo averli trascinati nell'apposito box.
   - Le interrogazioni in questa modalità si baseranno ESCLUSIVAMENTE sui documenti appena caricati (utile per estrazione dati, controlli incrociati e sintesi).
   - Puoi svuotare la memoria temporanea in qualsiasi momento usando il tasto "Pulisci Memoria Documenti".

3. **Analisi Ibrida (Documenti + Leggi)**:
   - Richiede di aver prima caricato ed elaborato dei documenti privati (come al punto 2).
   - Permette di fare domande molto approfondite in cui l'IA incrocia i dati del tuo documento (es. bilancio) con le regole imposte dalla normativa istituzionale locale (es. codice civile).
   - Nella risposta, l'Intelligenza Artificiale preciserà chiaramente da quale delle due fonti ha prelevato le varie informazioni.

### Requisiti e Istruzioni per l'Avvio:

0. **Prerequisito Critico**: L'applicazione **Ollama** deve essere in esecuzione in background sul tuo Mac (di default con il modello `llama3` installato).
   - *Nota sul Modello AI*: Se possiedi o preferisci utilizzare un altro modello tramite Ollama (es. `mistral` o `gemma`), lo script funzionerà perfettamente. Devi solo aprire il file `app.py` e cercare la riga `LLM_MODEL_NAME = "llama3"` sostituendola.

### 1. Installazione Generale (Linux / Windows / Cloud)
Per avviare l'app grafica su macchine standard:

1. Apri un terminale.
2. Posizionati all'interno della cartella:

   ```bash
   cd step5_graphical_inference
   ```

3. Crea e attiva l'ambiente:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # (Oppure venv\Scripts\activate su Windows)
   pip install -r requirements.txt
   ```

4. Esegui l'app con Streamlit:

   ```bash
   streamlit run app.py
   ```

### 2. Installazione Specifica per Sistemi macOS
Per l'utilizzo su sistemi Mac con chip Intel o Apple Silicon:

1. Apri il Terminale.
2. Vai nella cartella:

   ```bash
   cd step5_graphical_inference
   ```

3. **Solo ed esclusivamente la prima volta**, installa l'ambiente:

   ```bash
   chmod +x setup_env.sh && ./setup_env.sh
   ```

4. Per ogni sessione successiva, avvia così:

   ```bash
   source venv/bin/activate
   streamlit run app.py
   ```

### 3. Nota Specifica: MacBook Air M1 (8GB RAM)
⚠️ **Avvertenze sull'inferenza Modello Ibrido per Mac M1 (8GB):** 

* **Il peso dell'Interfaccia Grafica:** Oltre alle due IA già menzionate nello Step 4 (modello Vettoriale ed LLM in Ollama), questo step aggiunge il peso (minimo ma tangibile) del server web locale `Streamlit`. La memoria unificata da 8GB sarà sottoposta a Swap sul disco SSD. Valgono in modo assoluto le direttive precedenti: **Browser leggeri, chiudere altre applicazioni.**
* **Analisi Ibrida (Stress Test):** Se usi l'opzione "Analisi Ibrida (Documenti + Leggi)" e carichi un tuo contratto PDF privato molto lungo (es. 50 pagine), lo script andrà a vettorializzare "al volo" questo contratto saturando ulteriormente la RAM in quegli istanti. Sii paziente e non aprire altri programmi mentre l'interfaccia dice "Elaborazione in corso...".
* **Dissipazione:** Streamlit di per sé non scalda la macchina, vale lo stesso principio della chat: la temperatura salirà solo nei 20 secondi in cui l'IA formula la risposta testuale a schermo.

Quando hai finito di usare l'interfaccia:
- Torna nel terminale e premi `Ctrl+C` per fermare Streamlit.
- Digita `deactivate` per uscire.
- *Nota bene: NESSUN documento privato verrà conservato dopo lo spegnimento, a garanzia della massima privacy.*

### 4. Installazione Specifica per Sistemi ad Alte Prestazioni (Acer Veriton VN100 / Nvidia GB10 Blackwell)

Se disponi di una workstation avanzata come l'**Acer Veriton VN100** equipaggiato con processore **Nvidia Blackwell**, è stato creato uno script dedicato (`app_dgx.py`) che sfrutta al massimo l'architettura CUDA per l'elaborazione dei vettori e offre un monitoraggio accurato in tempo reale della VRAM.

L'installazione deve mantenere tutto il necessario all'interno della cartella corrente in un ambiente virtuale isolato (`venv`).

**I. OPERAZIONI DA ESEGUIRE SOLO LA PRIMA VOLTA (Installazione)**

Questi passaggi servono a preparare l'ambiente e vanno eseguiti **solo una volta**:

1. Apri un terminale e vai nella cartella del progetto:
   ```bash
   cd /home/max/Documenti/programmazione/ai_project/AI_professionisti/step5_graphical_inference
   ```

2. Crea l'ambiente virtuale isolato (`venv`) all'interno della cartella:
   ```bash
   python3 -m venv venv
   ```

3. Attiva l'ambiente virtuale:
   ```bash
   source venv/bin/activate
   ```

4. Installa le dipendenze locali:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   *(Nota: per sfruttare appieno Blackwell, assicurati che la versione di `torch` installata da pip supporti l'ultima versione di CUDA compatibile con la tua GPU. In genere su Linux si esegue anche un comando come `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121` se necessario).*

5. Termina la configurazione uscendo dall'ambiente:
   ```bash
   deactivate
   ```

---

**II. OPERAZIONI DA ESEGUIRE OGNI VOLTA CHE VUOI USARE L'APP**

Segui questi passaggi ogni volta che desideri avviare l'assistente:

1. Apri il terminale e vai nella cartella del progetto:
   ```bash
   cd /home/max/Documenti/programmazione/ai_project/AI_professionisti/step5_graphical_inference
   ```

2. Attiva l'ambiente virtuale:
   ```bash
   source venv/bin/activate
   ```

3. Avvia l'interfaccia grafica ottimizzata:
   ```bash
   streamlit run app_dgx.py
   ```

**Quando hai finito di usare l'interfaccia:**
- Torna nel terminale e premi `Ctrl+C` per fermare il server Streamlit.
- Disattiva sempre l'ambiente virtuale digitando:
  ```bash
  deactivate
  ```

---

**Vantaggi dell'ottimizzazione in `app_dgx.py`**:
- **Accelerazione CUDA Diretta**: `device='cuda'` configurato esplicitamente per il modello di embedding, bypassando calcoli lenti su CPU.
- **Monitoraggio GPU Real-Time**: Interroga i sensori Nvidia tramite `nvidia-smi` per darti l'esatto utilizzo percentuale del core Blackwell e la VRAM allocata direttamente nella barra laterale di Streamlit.
- **Isolamento e Pulizia**: Il progetto resta incapsulato e sicuro nella sua directory, senza necessità di installare librerie a livello di sistema operativo.

---

**III. SVILUPPI FUTURI: OTTIMIZZAZIONE AVANZATA DEL SISTEMA RAG**

Attualmente il sistema estrae un numero fisso di documenti (Top-K) dalla banca dati vettoriale. Per superare questo limite e implementare una logica di estrazione ultra-selettiva ("prendi solo quello che serve davvero"), le evoluzioni consigliate per l'architettura sono:

### 1. Metodo Re-Ranking (Cross-Encoder) --> RACCOMANDATO
Questa è la soluzione standard e definitiva per i sistemi RAG in produzione (Enterprise). I database vettoriali sono velocissimi nella ricerca per vicinanza semantica, ma faticano a cogliere le sfumature logiche complesse.
- **Funzionamento:** Si estraggono inizialmente un numero molto elevato di frammenti grezzi (es. i primi 40) tramite ChromaDB. Successivamente, si utilizza un modello AI specializzato e leggero chiamato **Re-ranker** (es. *bge-reranker*). Questo modello incrocia testualmente la domanda esatta dell'utente con ogni singolo frammento, assegnando un punteggio di pertinenza logica assoluta. Il sistema scarta poi tutti i documenti irrilevanti sotto una certa soglia e passa al LLM principale solo i frammenti strettamente necessari.
- **Vantaggi:** Estrema precisione e abbattimento totale del rumore di fondo. Il LLM riceve solo informazioni vitali, azzerando le allucinazioni.

### 2. Metodo Agenti Autonomi (Agentic RAG / ReAct)
Invece di utilizzare una pipeline lineare (Ricerca singola -> Generazione), si trasforma il sistema in un **Agente Autonomo** capace di ragionare a cicli.
- **Funzionamento:** L'LLM principale riceve la domanda dell'utente e decide autonomamente *cosa* cercare nel database. Dopo la prima ricerca, legge i risultati e si auto-valuta: *"Ho abbastanza informazioni per l'analisi completa? No, mi mancano i dettagli sull'art. 10-bis"*. A quel punto, genera da solo una seconda query di ricerca mirata. Quando ritiene di aver raccolto tutto e solo il contesto necessario, interrompe la ricerca ed elabora la risposta finale.
- **Vantaggi:** Capacità di astrazione altissima. Perfetto per risolvere problemi complessi multi-step che richiedono di incrociare norme distanti tra loro.
- **Svantaggi:** Complessità di implementazione (richiede orchestratori specifici) e tempi di generazione più lunghi dovuti ai molteplici cicli di pensiero.
