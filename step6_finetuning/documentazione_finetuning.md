# Step 6: Fine-Tuning Modello "Commercialista"

Questo documento traccia la strategia e la procedura "step-by-step" per effettuare il fine-tuning di un LLM. L'obiettivo è infondere al modello lo stile, il linguaggio tecnico e il ragionamento deduttivo testuale tipico di un Commercialista e Revisore Contabile italiano.

---

## 1. Il "Pensiero del Commercialista" (Instruction Tuning)

Il fine-tuning in questa fase serve per insegnare al modello *come* rispondere, non necessarimente *cosa* sapere a memoria (per quello hai già il tuo sistema RAG). Serve il cosiddetto **Instruction Tuning**.

Viene preparato un *Dataset* (es. 500-1000 domande/risposte) salvato in tre file JSONL: `train.jsonl` (addestramento) e `valid.jsonl` (verifica).

---

## 2. Preparazione del Dataset (Generale)

1. Usare i documenti Legali (Step 1 e 2).
2. Scrivere uno script Python che, tramite API o modelli in locale, auto-generi centinaia di finti "Casi Studio cliente-commercialista".
3. Salvare tutto formattato ad-hoc nei file `data/train.jsonl` e `data/valid.jsonl`.
4. Revisionare le risposte a mano: lo stile appreso nel testo sarà replicato al 100% dal modello finale.

---

## 3. Requisiti e Installazione

Il fine-tuning richiede risorse computazionali significative. Di seguito le istruzioni in base all'hardware a disposizione:

### 3.1 Installazione Generale (Linux / Windows / Cloud)

Per server cloud, macchine Linux o PC Windows con schede video NVIDIA (es. RTX 3090, 4090 o GPU Datacenter come le A100/H100), l'approccio standard prevede l'uso dell'ecosistema **PyTorch** e **HuggingFace** (in particolare le librerie `transformers`, `peft` e `trl`).

* **Requisiti:** Una GPU NVIDIA con almeno 16-24GB di VRAM per modelli fino a 8B parametri, installazione dei driver CUDA.
* **Installazione dell'ambiente:**

  ```bash
  python3 -m venv finetune_env
  source finetune_env/bin/activate
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
  pip install transformers datasets peft trl accelerate bitsandbytes
  ```

* **Vantaggi:** Tempi di addestramento ridotti e massimo supporto dalla community AI.

### 3.2 Installazione Specifica per Sistemi macOS

Se si utilizza un Mac moderno con processore Apple Silicon (M1, M2, M3, M4 - versioni Pro, Max o Ultra) e una buona dotazione di memoria unificata (es. 32GB, 64GB o 128GB), è altamente consigliato utilizzare il framework nativo di Apple: **MLX**. MLX è ottimizzato per sfruttare l'architettura a memoria unificata di Apple.

* **Requisiti:** macOS aggiornato, chip Apple Silicon, memoria unificata in base alle dimensioni del modello (almeno 16-32GB per stare sicuri).
* **Installazione dell'ambiente:**

  ```bash
  python3 -m venv mlx_env
  source mlx_env/bin/activate
  pip install mlx-lm datasets
  ```

* **Avvio del Fine-Tuning (Esempio MLX):**
  Il calcolo avverrà tramite `mlx_lm.lora`, sfruttando tutti i core della GPU integrata.

### 3.3 Nota Specifica: MacBook Air M1 (8GB RAM)

**Attenzione alle limitazioni hardware:** Svolgere l'addestramento su una macchina con 8GB di memoria RAM unificata presenta limiti severi, ma **è realizzabile** sfruttando l'ecosistema nativo Apple MLX e accettando *tempistiche di calcolo molto prolungate*.

* **Il limite della RAM (8GB):** Durante il training, gli 8GB fisici si satureranno istantaneamente. macOS inizierà a utilizzare lo "Swap Disk" (memoria virtuale sul disco SSD). Questo eviterà il blocco del PC, ma rallenterà radicalmente l'addestramento. È indispensabile chiudere **tutte le altre applicazioni** (browser inclusi) prima di iniziare.
* **Modelli Trattabili:** Il limite logico per addestrare è un modello **tra 1.5B e 3B parametri** (Es. `Llama-3.2-3B`), obbligatoriamente quantizzato a 4-bit (QLoRA).
* **Thermal Throttling:** Il MacBook Air M1 è sprovvisto di ventole attive. Scrivendo continuamente su disco e calcolando per ore, andrà in *Thermal Throttling* (abbasserà le frequenze per non surriscaldarsi), dilatando ulteriormente i tempi. Si raccomanda di tenerlo sollevato e ben areato.
* **Configurazione Obbligatoria del comando MLX:**
  Bisogna impostare un `batch-size` estremamente basso, altrimenti il Mac andrà in crash per mancanza di memoria.

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

  Partire con `--iters 400` come primo esperimento test. Aggiustare in seguito al rialzo solo in caso di esiti positivi del test.

---

## 4. Fusione dei Pesi (Dequantizzazione FP16) - Solo per ambiente MLX

A fine calcolo, se hai utilizzato MLX, avrai generato una cartella `adapters/` contenente solo la "conoscenza specializzata" del commercialista. Per poterla usare facilmente nell'ecosistema Ollama, bisogna fondere il modello decomprimendolo nel formato standard (FP16).

```bash
mlx_lm.fuse \
  --model mlx-community/Llama-3.2-3B-Instruct-4bit \
  --adapter-path adapters \
  --dequantize \
  --save-path ./commercialista_mlx_fp16
```

Il disco lavorerà per un paio di minuti e genererà una nuova cartella `commercialista_mlx_fp16` da circa 6.5 GB.

---

## 5. Integrazione su Ollama

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
