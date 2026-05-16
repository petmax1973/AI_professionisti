# Step 6: Fine-Tuning Modello "Commercialista"

Questo documento traccia la strategia e la procedura "step-by-step" per effettuare il fine-tuning di un LLM. L'obiettivo è infondere al modello lo stile, il linguaggio tecnico e il ragionamento deduttivo testuale tipico di un Commercialista e Revisore Contabile italiano.

---

## 1. Informazioni Generali sul Fine-Tuning

### 1.1 Il "Pensiero del Commercialista" (Instruction Tuning)

Il fine-tuning in questa fase serve per insegnare al modello *come* rispondere, non necessarimente *cosa* sapere a memoria (per quello hai già il tuo sistema RAG). Serve il cosiddetto **Instruction Tuning**.

Viene preparato un *Dataset* (es. 500-1000 domande/risposte) salvato in tre file JSONL: `train.jsonl` (addestramento) e `valid.jsonl` (verifica).

### 1.2 Preparazione del Dataset

1. Usare i documenti Legali (Step 1 e 2).
2. Scrivere uno script Python che, tramite API o modelli in locale, auto-generi centinaia di finti "Casi Studio cliente-commercialista".
3. Salvare tutto formattato ad-hoc nei file `data/train.jsonl` e `data/valid.jsonl`.
4. Revisionare le risposte a mano: lo stile appreso nel testo sarà replicato al 100% dal modello finale.

---

## 2. Percorso A: NVIDIA DGX Spark GB10 (Blackwell) — QLoRA in FP4

Questo sistema rappresenta l'avanguardia per l'Intelligenza Artificiale. Grazie all'architettura **Blackwell** e ai 128 GB di **memoria unificata** (condivisa tra CPU e GPU), il fine-tuning di modelli fino a 32B parametri è possibile direttamente in locale.

> **⚠️ Nota Tecnica — Memoria Unificata:**
> L'Acer Veriton VN100 GB10 utilizza un'architettura a **memoria unificata**: i 128 GB di RAM sono condivisi tra CPU e GPU. Se il training alloca troppa memoria, il sistema operativo va in swap e il PC si blocca. I parametri nello script `train_dgx.py` sono stati calibrati per evitare questo problema.

### 2.1 Tecnica: QLoRA (Quantized LoRA)

Lo script utilizza **QLoRA**: il modello base viene caricato **quantizzato in FP4** (4-bit nativo Blackwell) e solo piccoli adapter LoRA vengono addestrati. Questo riduce la memoria necessaria da ~64 GB (FP16 completo) a ~20 GB.

* **Vantaggi dell'Architettura Blackwell (Supporto Nativo FP4):** I nuovi Tensor Core introducono il supporto **nativo al formato FP4** (4-bit floating point). A differenza dei sistemi precedenti dove la quantizzazione a 4-bit gravava sui core standard, Blackwell esegue calcoli matriciali in FP4 direttamente via hardware. Questo raddoppia le prestazioni rispetto all'FP8 e riduce drasticamente l'uso della VRAM.

### 2.2 Preparazione dell'Ambiente (Una tantum)

  ```bash
  python3 -m venv venv_blackwell
  source venv_blackwell/bin/activate
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
  pip install transformers datasets peft trl accelerate bitsandbytes
  ```

### 2.3 Parametri Chiave dello Script

I parametri in `train_dgx.py` sono stati calibrati per il GB10 con memoria unificata:

| Parametro | Valore | Motivazione |
|---|---|---|
| `per_device_train_batch_size` | 1 | Batch conservativo per non saturare la RAM unificata |
| `gradient_accumulation_steps` | 8 | Compensa il batch piccolo (effective batch = 8) |
| `max_seq_length` | 1024 | Limita le sequenze (il dataset contiene testi fino a 57K token) |
| `gradient_checkpointing` | True | Scambia velocità per memoria (~60% meno RAM) |
| `optim` | `adamw_8bit` | Optimizer a 8-bit: dimezza la RAM dell'optimizer |
| `max_memory` | 100 GiB | Lascia ~28 GB liberi per il sistema operativo |

### 2.4 Avvio dell'Addestramento (Ogni volta)

**Prerequisito:** All'apertura di ogni nuovo terminale, attivare prima l'ambiente virtuale. Se nel terminale vedi già il prefisso `(venv_blackwell)`, puoi saltare questo passaggio.

```bash
source venv_blackwell/bin/activate
```

Una volta attivato, lanciare lo script di addestramento:

```bash
python3 train_dgx.py
```

Lo script stampa a video lo stato di avanzamento e il consumo di memoria. Con il dataset attuale (~900 campioni, 3 epoche), l'addestramento richiede circa 1-2 ore.

### 2.5 Fusione dei Pesi (Ogni volta)

Terminato il fine-tuning, i pesi dell'adapter specializzato saranno salvati nella cartella di output (es. `outputs/`). **Nella stessa sessione di terminale** (l'ambiente è ancora attivo), lancia lo script di fusione:

```bash
python3 merge_dgx.py
```

Verrà creata la cartella `commercialista_blackwell_merged` contenente i pesi integrati pronti per Ollama.

### 2.6 Integrazione su Ollama

1. Creare un file testuale chiamato `Modelfile` (nella cartella `step6_finetuning`) con questo contenuto:
    ```dockerfile
    FROM ./commercialista_blackwell_merged
    PARAMETER temperature 0.1
    ```
2. Importare il modello in Ollama con quantizzazione **Q8_0** (consigliata per il GB10 con 128 GB di RAM):
    ```bash
    # Q8_0 — Consigliato: qualità quasi identica a BF16, ~34 GB di RAM
    ollama create mio_commercialista -f Modelfile --quantize q8_0

    # Alternative (scegliere UNA sola):
    # Q6_K — Ottimo compromesso qualità/memoria, ~26 GB di RAM
    # ollama create mio_commercialista -f Modelfile --quantize q6_k

    # Q4_K_M — Buon compromesso, più leggero, ~20 GB di RAM
    # ollama create mio_commercialista -f Modelfile --quantize q4_k_m

    # Senza flag — mantiene BF16 pieno, ~64 GB di RAM
    # ollama create mio_commercialista -f Modelfile
    ```
3. Lanciare il modello specializzato:
    ```bash
    ollama run mio_commercialista
    ```

> **Nota sulla quantizzazione:** Il merge produce pesi in BF16 (~64 GB). Ollama li converte in formato GGUF
> applicando la quantizzazione scelta. Le opzioni disponibili sono:
>
> | Flag | RAM stimata (32B) | Qualità | Note |
> |------|-------------------|---------|------|
> | `q8_0` | ~34 GB | ⭐⭐⭐⭐⭐ | **Consigliato per GB10** — qualità quasi identica al BF16 |
> | `q6_k` | ~26 GB | ⭐⭐⭐⭐ | Ottimo compromesso |
> | `q4_k_m` | ~20 GB | ⭐⭐⭐⭐ | Buon compromesso, più leggero |
> | *(nessuno)* | ~64 GB | BF16 pieno | Massima qualità ma occupa metà della RAM |

---

## 3. Percorso B: Apple Silicon (Mac M-Series)

Se si utilizza un Mac moderno con processore Apple Silicon (M1, M2, M3, M4 - versioni Pro, Max o Ultra) e una buona dotazione di memoria unificata (es. 32GB, 64GB o 128GB), è altamente consigliato utilizzare il framework nativo di Apple: **MLX**. MLX è ottimizzato per sfruttare l'architettura a memoria unificata.

### 3.1 Preparazione dell'Ambiente (Una tantum)

* **Installazione dell'ambiente:**
  Per mantenere l'isolamento all'interno di questo step (come nel resto del progetto), puoi eseguire lo script preparato:
  ```bash
  chmod +x setup_env.sh
  ./setup_env.sh
  ```
  *(Oppure, se preferisci procedere manualmente: `python3 -m venv venv && source venv/bin/activate && pip install mlx-lm datasets`)*

* **Nota Specifica per MacBook Air M1 (8GB RAM):**
  Svolgere l'addestramento su una macchina con soli 8GB di memoria RAM unificata presenta limiti severi, ma **è realizzabile** sfruttando l'ecosistema nativo Apple MLX e accettando *tempistiche di calcolo molto prolungate*.
  * Il limite della RAM (8GB): Durante il training, gli 8GB fisici si satureranno istantaneamente. macOS inizierà a utilizzare lo "Swap Disk" (memoria virtuale sul disco SSD). Questo eviterà il blocco del PC, ma rallenterà radicalmente l'addestramento. **È indispensabile chiudere tutte le altre applicazioni** (browser inclusi) prima di iniziare.
  * Modelli Trattabili: Il limite logico per addestrare è un modello **tra 1.5B e 3B parametri** (Es. `Llama-3.2-3B`), obbligatoriamente quantizzato a 4-bit (QLoRA).
  * Thermal Throttling: Il MacBook Air M1 è sprovvisto di ventole attive. Scrivendo continuamente su disco e calcolando per ore, abbasserà le frequenze per non surriscaldarsi. Si raccomanda di tenerlo sollevato e ben areato.

### 3.2 Avvio dell'Addestramento (Ogni volta)

Il calcolo avverrà tramite il comando CLI `mlx_lm.lora`, sfruttando tutti i core della GPU integrata.
**Attenzione (per Mac con 8GB di RAM):** Bisogna impostare un `batch-size` estremamente basso (es. 1), altrimenti il Mac andrà in crash per mancanza di memoria. Partire con `--iters 400` come primo esperimento test.

```bash
mlx_lm.lora \
  --model mlx-community/Llama-3.2-3B-Instruct-4bit \
  --train \
  --data ./data \
  --iters 400 \
  --batch-size 1 \
  --num-layers 4 \
  --max-seq-length 512
```

### 3.3 Fusione dei Pesi (Ogni volta)

A fine calcolo, se hai utilizzato MLX, avrai generato una cartella `adapters/` contenente solo la "conoscenza specializzata" del commercialista. Per poterla usare facilmente nell'ecosistema Ollama, bisogna fondere il modello decomprimendolo nel formato standard (FP16):

```bash
mlx_lm.fuse \
  --model mlx-community/Llama-3.2-3B-Instruct-4bit \
  --adapter-path adapters \
  --dequantize \
  --save-path ./commercialista_mlx_fp16
```

Il disco genererà una nuova cartella `commercialista_mlx_fp16` da circa 6.5 GB.

### 3.4 Integrazione su Ollama

1. Creare un file testuale chiamato `Modelfile` (nella cartella `step6_finetuning`) con questo contenuto:
    ```dockerfile
    FROM ./commercialista_mlx_fp16
    PARAMETER temperature 0.1
    ```
2. Importare e lanciare il modello finito in Ollama:
    ```bash
    ollama create mio_commercialista -f Modelfile
    ollama run mio_commercialista
    ```
