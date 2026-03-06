# Guida Definitiva: Sistemi AI Locali per Professionisti

## Un percorso completo dalla progettazione alla realizzazione quotidiana

### Descrizione Generale del Progetto

L'obiettivo di questo progetto è la realizzazione di un ecosistema AI verticale (specializzato per settore) che permetta a professionisti come **commercialisti, avvocati, medici e amministratori di condominio** di elaborare grandi moli di dati sensibili in **totale privacy**. A differenza delle IA in cloud (ChatGPT), questa soluzione opera interamente **offline** su hardware locale, garantendo la conformità al GDPR e la protezione del segreto professionale. Il sistema si basa su una strategia ibrida: **Fine-Tuning** per il linguaggio tecnico e **RAG (Retrieval-Augmented Generation)** per la consultazione di leggi e fascicoli clienti.

---

## 🛠 Percorso di Realizzazione in 7 Step

### STEP 1: Architettura Hardware e Budgeting

Si adotta una rigorosa divisione architetturale tra "Factory" (per lo sviluppo) e "Client" (per l'uso quotidiano in studio). Questa divisione è fondamentale per la sostenibilità economica e tecnica del progetto.

* **Factory Server (Lo Sviluppatore / L'Agenzia)**: **NVIDIA Spark DGX** o similari (es. **ASUS Ascent GX10** con Blackwell GPU da ~1 PetaFLOP e 128GB RAM unificata). Viene utilizzato per addestrare i modelli tramite QLoRA. Non è necessario in ogni studio professionale, ne basta uno centrale. *Investimento est: €3.000–€5.000*.
* **Edge Client (Il Professionista)**: **MINIS FORUM MS-S1 Max** (AMD Ryzen AI Max+ 395, 128GB UMA RAM). Questo PC viene fisicamente installato nello studio dell'avvocato o commercialista. Non esegue addestramenti pesanti, ma utilizza la sua CPU/RAM per far girare il modello specializzato (Inference) e gestire il RAG locale sui dati dei clienti. *Investimento est: €3.000*.
* **Sistema Operativo**: **Ubuntu Linux** per la Factory (stack CUDA/AI ottimizzato); **Windows 11 Pro** per il Client (standard de facto degli studi professionali, essenziale per compatibilità con i loro gestionali storici).

### STEP 2: Acquisizione Dati (Harvesting)

Evitare lo scraping web, fragile e legalmente rischioso. Utilizzare fonti ufficiali e strutturate per ottenere XML puliti e completi:

* **Normattiva API (Open Data & SOAP)**: La via maestra per ottenere dati strutturati.
  * *Documentazione Completa*: Consulta il file dedicato [API Normattiva Open Data](normattiva_api_docs.md) per tutti gli endpoint REST, i parametri di ricerca avanzata, l'esportazione asincrona e i comandi `curl` di esempio.
  * *Esempio di automazione*: Workflow **n8n** (Schedule Trigger -> API REST `Ricerca Avanzata` o SOAP `getLegge` -> Salva XML) per intercettare automaticamente i nuovi decreti (vedi endpoint *Ricerca Atti Aggiornati* nella documentazione).
  * *Identificativo consigliato*: Utilizzare i metadati forniti dalle API come `codiceRedazionale` o la composizione `tipo + anno + numero` (es. `LEGGE-2024-123`) per evitare duplicati nel database.
  * *Testi chiave*: TUIR (Testo Unico Imposte sui Redditi), DPR IVA (633/72), Codice Civile (parte societaria).
* **Open Data Ufficiali**: Strumenti preziosissimi per creare casi d'uso realistici:
  * `dati.gov.it`: Dataset pubblici convertibili in casi d'uso jsonl.
  * `OpenBDAP` e `OpenCoesione`: Fondamentali per far "capire" i bilanci all'IA.
  * Open Data Regionali (es. `dati.campania.it` su evasioni, redditi 730/UNICO).
* **Fonti Ag. Entrate**: Download di Circolari, Risoluzioni e istruzioni modelli (PDF -> OCR -> Testo). Le circolari sono essenziali per il lato pratico-interpretativo. Importante usare tool OCR o script Python per ripulire header e footer prima di passarli al blocco AI.

### STEP 3: Preparazione e Chunking (Preprocessing)

I testi devono essere "masticati" correttamente dall'AI:

* **Pulizia**: Rimozione di tag tecnici XML/HTML e boilerplate.
* **Recursive Chunking**: Dividere i testi in blocchi da **1000-1500 caratteri** con una sovrapposizione (**overlap**) di **150-200 caratteri** per non perdere il contesto tra i blocchi.
* **Metadata**: Associare a ogni blocco l'identificativo unico (es. `LEGGE-2024-123`).

### STEP 4: Sintesi del Dataset (Il "Maestro")

Utilizzare un modello potente (**Llama 3 70B**) sulla macchina Factory per convertire o generare materiale formativo, diviso logicamente in categorie:

1. **Q&A Reali / Ragionamento pratico (Cruciale)**: Domande di clienti ("Come calcolo l'IVA?"), pareri, interpelli. Insegna al modello *come* pensare e rispondere.
2. **Casi studio/Documenti**: Contratti, atti, bilanci anonimizzati.

**Processo di Generazione**:

* Passare i concetti normativi estratti al modello Llama 3 70B e fargli generare 3-5 coppie di **Domanda/Risposta tecnica**.
* Salvare il risultato in formato **JSONL** con struttura `instruction` (la domanda), `input` (il contesto/riferimento di legge), e `output` (la risposta spiegata).
* **Dimensione Consigliata**: Per un modello realmente professionale ed esperto di un dominio, puntare a un dataset compreso tra i **20.000 (Buono) e i 50.000 (Eccellente)** esempi di alta qualità. Non sono necessari milioni di record.

### STEP 5: Addestramento locale (Fine-Tuning e QLoRA)

Insegnare al modello locale il ragionamento, il tono e la terminologia del settore (NON fargli memorizzare a memoria le leggi), partendo dai migliori LLM base open-weight:

* **Modelli Consigliati**:
  * **Meta Llama 3 70B**: Eccellente ragionamento, lo "sweet spot" per i professionisti (tempo stimato su GX10: 30-60 ore).
  * **Alibaba Qwen 2.5 32B**: Molto efficiente, addestramento veloce (12-24h su GX10), ideale per avviare la pipeline risparmiando memoria.
* **Architettura**: Puoi creare un modello per ogni ruolo (es. Modello-Penalista, Modello-Commercialista) per la massima precisione, oppure un modello unificato a cui passi il "ruolo" via prompt (più semplice da gestire).
* **Librerie e Metodo**: Usare **Unsloth** per velocizzare il training su NVIDIA. Applicare **QLoRA (8-bit)** per aggiornare solo i pesi (adapter) senza saturare i 128GB di RAM.
* **Esportazione**: Unire gli adattatori al modello base (**Merging**) in un'unica cartuccia finale quantizzata in formato **GGUF** (4/5/6-bit), rendendo il deployment sul Mini PC del cliente "plug & play".

### STEP 6: Deployment e Interfaccia (Ollama & Flutter)

Fornire al professionista uno strumento semplice da usare:

* **Inference Engine**: **Ollama** eseguito localmente per servire il modello GGUF via API compatibili con OpenAI.
* **Frontend (Flutter)**: Un'applicazione desktop reattiva e professionale (simile visivamente a ChatGPT, ma totalmente privata) progettata per l'uso quotidiano in studio. Gestisce:
  * **Interfaccia di Chat Offline**: Una finestra di dialogo fluida dove il professionista può interrogare il modello locale sul caso in esame, con risposte in streaming in tempo reale.
  * **Caricamento Documenti Locali (RAG On-Demand)**: Il professionista può trascinare (drag&drop) i PDF dei clienti o della pratica (es. bilanci, contratti, cartelle cliniche, fascicoli processuali) direttamente nell'app. Questi documenti vengono elaborati e "letti" dal sistema vettoriale locale istantaneamente.
  * **Privacy Assoluta**: Essendo tutto gestito offline sul PC locale, non vi è alcun rischio nel caricare dati personali o estremamente sensibili dei clienti. Nessun dato lascia mai le mura dello studio, garantendo il pieno rispetto del Segreto Professionale e della normativa GDPR.
  * **Interrogazione Contestuale**: L'IA risponde alle domande incrociando la sua competenza tecnica (dal Fine-Tuning) con i dati specifici del cliente appena caricati (tramite RAG). Alcuni esempi pratici di utilizzo:
    * *Studio Legale*: "Trova tutte le incongruenze nelle testimonianze presenti in questo fascicolo di 500 pagine" oppure "Verifica se questo contratto di locazione include clausole vessatorie non a norma di legge".
    * *Studio Commerciale*: "Confronta il bilancio 2022 e 2023 di questa azienda, evidenziando le voci di spesa aumentate in modo anomalo" oppure "Analizza questo estratto conto e raggruppa le spese per fornitore".
    * *Studio Medico*: "Riassumi la storia clinica del paziente basandoti su questi 20 referti slegati e segnala in modo evidente allergie o controindicazioni ai FANS".
    * *Amministratore di Condominio*: "Verifica nel regolamento del Condominio X se è consentito installare tende da sole e, in caso, quali maggioranze servono per le modifiche di facciata".

---

## 🔒 Focus Privacy e Zero Costi: AI Locale vs Cloud (ChatGPT)

### 1. Il Vantaggio della Privacy Assoluta

L'adozione dell'AI nel settore professionale (avvocati, medici, commercialisti) è bloccata dalla **Privacy e dal Segreto Professionale**.
Caricare dati sensibili (dati identificativi, clinici o di procedure penali/civili) su ChatGPT standard viola il GDPR perché:

* I server sono spesso Extra-UE.
* C'è il rischio di riutilizzo dei dati per successivi addestramenti.
* Non vi è alcun **Data Processing Agreement (DPA)** in grado di tutelare legalmente il professionista (che rimane il titolare del trattamento).
Un utilizzo del cloud prevede sanzioni, responsabilità disciplinari e civili per il professionista.

Una **Stazione di Lavoro AI Locale** risolve il problema alla radice perché **nulla esce dalla macchina**:

1. Non vi è alcun trasferimento a terzi, mantenendo intatto il rapporto fiduciario e il segreto professionale.
2. Tramite **Windows BitLocker**, un firewall per limitare il traffico esterno e la disattivazione della telemetria, il PC si trasforma in una cassaforte a norma (ex Art. 32 GDPR).
3. Non è richiesto alcun consenso ulteriore al cliente se l'elaborazione avviene offline per uso interno associato strettamente alla gestione della sua pratica.

### 2. L'Abbattimento Totale dei Costi Ricorrenti (Nessun Token)

Oltre all'imprescindibile vantaggio della privacy, essendo il sistema completamente autonomo con un modello in esecuzione locale, si ottiene uno straordinario **vantaggio economico**:

* **Assenza di consumo token**: A differenza delle API di modelli cloud (come OpenAI), non si paga per il volume testuale elaborato. Passare al setaccio interi fascicoli di migliaia di pagine avviene a costo zero.
* **Nessun abbonamento**: Non vi è alcun canone ricorrente mensile.
* **Elaborazioni intensive a "costo solo corrente"**: È possibile pianificare compiti titanici, come far riassumere cause decennali, far verificare centinaia di bilanci o far estrarre clausole da enormi moli di atti durante intere notti. Il sistema elabora ininterrottamente e l'unico esborso è costituito dall'elettricità consumata dal Mini PC, mettendo definitivamente al riparo lo studio da conti astronomici dei servizi API-based.

---

## �🔍 Focus Tecnico: Come implementare il RAG (Retrieval-Augmented Generation)

Il RAG è il "ponte" tra il cervello dell'IA (il modello, precedentemente istruito col Fine-Tuning a ragionare come un professionista) e i tuoi documenti privati mutevoli (leggi in continuo aggiornamento, fascicoli depositati ieri, circolari).

**Regola d'oro: Il Fine-Tuning fornisce il vocabolario, lo stile e la logica; il RAG fornisce la conoscenza legislativa fresca da consultare (Codice Civile, TUIR, Normattiva).**

Ecco il processo passo dopo passo per realizzarlo:

### 1. Ingestion e Preprocessing (Il Database Semantico)

Non basta "dare" un PDF all'IA. Bisogna trasformarlo in vettori matematici:

* **Parsing**: Estrarre il testo dai PDF (usando librerie come `PyMuPDF` o `Docling`).
* **Chunking**: Dividere il testo in blocchi semantici. Un approccio efficace è il **Recursive Character Text Splitter** (blocchi da ~1000 caratteri con 200 di overlap).
* **Embedding**: Passare ogni blocco a un modello locale (es. `bge-m3` o `nomic-embed-text`) che trasforma il testo in una lista di numeri (vettore) che ne rappresenta il significato.

### 2. Archiviazione (Vector DB Locale)

I vettori vengono salvati in un database specializzato:

* **Scelta**: **Qdrant** o **ChromaDB** in modalità locale/container.
* **Metadata**: Insieme al vettore, salva il testo originale e il riferimento alla fonte (es. "Art. 1 bis Legge 123/24").

### 3. Recupero (Semantic Search)

Quando l'utente fa una domanda:

1. La domanda viene trasformata in un **vettore** dallo stesso modello di embedding usato prima.
2. Il Vector DB confronta il vettore della domanda con quelli memorizzati (usando la **Cosine Similarity**).
3. Vengono estratti i **top-k** blocchi più rilevanti (es. i 3 articoli di legge più simili alla domanda).

### 4. Generazione Aumentata (The Prompt)

Il sistema costruisce un nuovo prompt per l'LLM:
> "Sei un assistente legale esperto. Rispondi alla domanda usando SOLO il contesto fornito. Se non sai la risposta, dillo.
>
> **CONTESTO**: [Blocco recuperato 1], [Blocco recuperato 2]
>
> **DOMANDA**: [Domanda dell'utente]"

### 5. Strumenti Consigliati

* **Framework**: **LangChain** o **LlamaIndex** (Python) per concatenare i passaggi.
* **Database**: **Qdrant** o **ChromaDB** (veloce e con ottima interfaccia web).
* **Modello di Embedding**: `nomic-embed-text` o `bge-m3` o `instructor` (estremamente leggeri ed efficienti via Ollama).

## ♻️ Ciclo di Vita del Sistema

Per mantenere l'intelligenza artificiale al massimo delle prestazioni, adotta un ciclo duale:

* **Quotidiano (RAG)**: Lo script di n8n scarica ogni giorno i nuovi provvedimenti/circolari e li aggiunge in automatico al Vector DB del cliente. Le risposte sull'ultimo decreto si aggiornano in tempo reale a costo zero.
* **Semestrale (Fine-Tuning)**: Se le prassi operative o le leggi base subiscono cambiamenti profondi, si riprende il server DGX Spark, si creano nuovi esempi JSONL, si lancia una nuova sessione di QLoRA (aggiornando la logica del cervello) e si fa l'aggiornamento del file GGUF presso i clienti.

### STEP 7: Privacy e Sicurezza Locale

Blindare il sistema per la massima tranquillità legale:

* **Firewall**: Bloccare ogni connessione internet in uscita dal Mini PC.
* **Cifratura**: Attivazione obbligatoria di **Windows BitLocker**.
* **No Logging**: Disattivare ogni telemetria software. Il professionista opera in un ambiente isolato (Art. 32 GDPR).

---

## 📈 Percorso Professionale: Diventare LLM Engineer

Per chi vuole realizzare e vendere queste soluzioni al mercato business (stipendi entry 35k€ - freelance oltre 500€/giornata):

* **Fase 1 (Mese 1)**: Base di programmazione Python (`json`, API, strutturazione dati con `pandas`).
* **Fase 2 (Mese 2)**: Prompt engineering e chiamate API verso modelli IA standard.
* **Fase 3 (Mese 2-3)**: Piattaforma **Hugging Face** (Librerie `transformers`, `datasets`, `peft`) per scaricare e strutturare pesi a livello codice. Sviluppo di applicazioni RAG (Retrieval-Augmented Generation) integrando database vettoriali come FAISS o ChromaDB.
* **Fase 4 (Mese 4-5)**: Implementazione reale di Fine-Tuning tramite PEFT/LoRA per specializzare realmente i modelli su contesti verticali. Uso di **Ollama** per execution su client offline.
* **Fase 5 (Mese 6 e oltre)**: Deployment tramite creazione di microservizi (FastAPI) o UI complete (Flutter/Gradio), e creazione di un proprio Portfolio Projects da presentare alle aziende o ai professionisti.

---

## 💡 Esempi Operativi

### A. Esempio Dataset per Fine-Tuning (Fiscale)

```jsonl
{"instruction": "Come si gestisce l'IVA per acquisti intra-UE?", "input": "Azienda IT acquista da DE", "output": "L'operazione avviene in reverse charge. L'acquirente integra la fattura con IVA e la registra sia negli acquisti che nelle vendite."}
```

### B. Esempio Risposta RAG (Legale)

**Domanda**: "Posso detrarre le spese di manutenzione straordinaria?"
**Processo RAG**: Il sistema recupera l'Art. 16-bis del TUIR dal database locale.
**Risposta**: "Sì, secondo l'Art. 16-bis del TUIR (Fonte locale), le spese sono detraibili al 50% fino a un tetto di 96.000€..."

### C. Richiesta SOAP Normattiva (Sourcing)

```xml
<soapenv:Envelope xmlns:urn="urn:LeggiService">
   <soapenv:Body>
      <urn:getLegge>
         <arg0>DPR</arg0>
         <arg1>1972</arg1>
         <arg2>633</arg2>
      </urn:getLegge>
   </soapenv:Body>

> 💡 *Nota: Per una panoramica completa di tutte le API REST JSON fornite da Normattiva, incluse le ricerche avanzate e l'export asincrono, consulta il documento separato [API Normattiva Open Data (normattiva_api_docs.md)](normattiva_api_docs.md).*
