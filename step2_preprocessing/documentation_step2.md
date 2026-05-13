# Obiettivo dello Step 2: Preprocessing per il RAG

> **Nota di automazione:** Se desideri eseguire questo step (assieme allo Step 1 e 3) in modo del tutto automatico e asincrono, fai riferimento allo script `run_pipeline.py` documentato nel README principale del progetto.

In questo step, i dati "grezzi" scaricati dal governo (JSON e PDF) vengono "appiattiti", puliti e arricchiti, convertendoli in frammenti di testo ("chunks") in formato JSONL ideali per essere "letti" dall'intelligenza artificiale (ricerca vettoriale).

Scegli il percorso di esecuzione più adatto al tuo hardware.

---

# PERCORSO 1: Esecuzione Standard (PC generici, Mac, Cloud)

Questa è la procedura standard. Utilizza gli script originali pensati per elaborare i file uno ad uno (in streaming iterativo), garantendo che il consumo di memoria RAM resti bassissimo anche se si elaborano decine di migliaia di leggi. 

È la scelta ideale per computer portatili (es. MacBook Air M1 8GB RAM), PC tradizionali e piccoli server cloud.

## 1. `preprocess_rag.py` (Leggi da Normattiva)

Questo script apre i file JSON complessi scaricati da Normattiva, estrae i metadati globali (Tipo Atto, Numero, Anno), naviga ricorsivamente per trovare **Articoli** e **Allegati**, e costruisce i chunk finali inserendo una testata semantica in ogni frammento (per dare contesto all'AI). 

**Installazione ed Esecuzione:**
Questo script utilizza *esclusivamente* le librerie standard di Python (`json`, `os`, `glob`), quindi non richiede installazioni tramite `pip`.

```bash
cd step2_preprocessing
python3 preprocess_rag.py
```

## 2. `preprocess_agenzia.py` (Documenti Agenzia delle Entrate)

Questo script estrae il testo dai file PDF dell'Agenzia delle Entrate usando `PyMuPDF`, sanitizza i caratteri di controllo "sporchi", e suddivide il testo in frammenti meccanici di 1500 caratteri (usando `RecursiveCharacterTextSplitter`). Ricostruisce inoltre i metadati analizzando il nome del file PDF.

**Installazione ed Esecuzione:**
Richiede un virtual environment e alcune librerie.

```bash
cd step2_preprocessing
# Crea l'ambiente virtuale e installa le dipendenze base
chmod +x setup_env.sh
./setup_env.sh

# Attiva l'ambiente e lancia lo script
source venv/bin/activate
python3 preprocess_agenzia.py
```

---

# PERCORSO 2: Esecuzione High-Performance (Acer Veriton / Grace-Blackwell)

Per sistemi workstation ad altissime prestazioni come l'**Acer Veriton GN100** (dotato di processore ARM Grace a 20 core e GPU Blackwell), sono stati introdotti due script speciali che sfruttano il **multiprocessing massivo** e l'**Intelligenza Artificiale locale** per abbattere drasticamente i tempi di elaborazione e migliorare la qualità semantica.

## 1. `preprocess_normativa_acer.py`
*(Dedicato a Normattiva)*
Lancia un `ProcessPoolExecutor` per scatenare tutti i 20 core della CPU Grace. Elabora decine di file JSON simultaneamente in parallelo, mantenendo intatto il rigoroso partizionamento giuridico (per Articoli/Allegati). Azzera il collo di bottiglia dovuto all'I/O del disco.

## 2. `preprocess_agenzia_acer.py`
*(Dedicato all'Agenzia delle Entrate)*
Esegue l'estrazione in parallelo dai PDF dai 20 core e applica il **Semantic Chunking**. Anziché tagliare il testo a 1500 caratteri in modo "meccanico", carica un modello di embedding AI (`all-MiniLM-L6-v2`) nella GPU Blackwell (o su CPU). L'AI analizza semanticamente le frasi e taglia i blocchi di testo solo al vero "cambio logico di argomento", migliorando enormemente la precisione per la successiva interrogazione LLM.

## Installazione ed Esecuzione (Acer Veriton)

Per utilizzare l'Intelligenza Artificiale locale, è necessario installare un file di requisiti aggiuntivo (`requirements_acer.txt`).

**Setup dell'ambiente (una tantum):**
```bash
# 1. Crea l'ambiente virtuale base (se non lo hai già fatto in precedenza)
chmod +x setup_env.sh
./setup_env.sh

# 2. Attiva l'ambiente
source venv/bin/activate

# 3. Installa le librerie avanzate per PyTorch e il Semantic Chunking (richiede ~500MB)
pip install -r requirements_acer.txt
```

**Esecuzione:**
```bash
# Assicurati di avere il venv attivo
source venv/bin/activate

# Elaborazione ultra-veloce Leggi (Multiprocessing 20-core)
python3 preprocess_normativa_acer.py

# Elaborazione AI Agenzia Entrate (GPU/CPU Semantic Chunking)
python3 preprocess_agenzia_acer.py
```

---

# Output Generato

Sia il Percorso 1 che il Percorso 2 generano esattamente gli stessi file di output, che verranno consumati dallo Step 3. I file JSONL sono creati in streaming riga per riga per prevenire crash di memoria.

```text
step2_preprocessing/accountant_rag_dataset/
├── dataset_rag_langchain.jsonl       ← Leggi da Normattiva 
└── dataset_agenzia_langchain.jsonl   ← Documenti Agenzia delle Entrate
```
