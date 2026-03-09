# Step 6: Fine-Tuning Modello "Commercialista" (100% Locale su Mac M1)

Questo documento traccia la strategia e la procedura "step-by-step" per effettuare il fine-tuning di un LLM **esclusivamente in locale** sul tuo Mac M1 (8GB RAM, 8 Core CPU, 7 Core GPU), senza appoggiarsi a server cloud esterni.

L'obiettivo è infondere al modello lo stile, il linguaggio tecnico e il ragionamento deduttivo testuale tipico di un Commercialista e Revisore Contabile italiano, accettando consapevolmente tempistiche di calcolo prolungate dovute allo Swap di sistema.

---

## 1. Sfide Hardware e Il Framework Apple MLX

Svolgere l'addestramento su una macchina con 8GB di memoria RAM unificata presenta limiti severi, ma **è realizzabile** sfruttando l'ecosistema nativo Apple.

* **Il limite della RAM (8GB):** Durante il training di un modello da 3 miliardi di parametri, gli 8GB fisici si satureranno istantaneamente. macOS inizierà a utilizzare lo "Swap Disk" (memoria virtuale sul disco SSD). Questo eviterà il blocco del PC, ma rallenterà radicalmente l'addestramento (il disco SSD è veloce, ma immensamente più lento della RAM).
* **Il Framework (Apple MLX):** Dimentichiamo PyTorch o librerie per server Nvidia. Useremo **MLX**, una libreria sviluppata direttamente dal team Machine Learning di Apple. È progettata per estrarre le massime prestazioni dai chip M1/M2/M3 e gestire nel modo più intelligente possibile l'architettura a memoria unificata, includendo il supporto nativo a QLoRA.
* **Modelli Trattabili:** Il limite logico per addestrare (anche lentamente) con 8GB è un modello **tra 1.5B e 3B parametri**. (Es. `Qwen2.5-1.5B` o `Llama-3.2-3B`).
* **Tecnica Obbligatoria (QLoRA):** Il modello dovrà essere quantizzato (compresso) a 4-bit in memoria durante il calcolo, e l'addestramento avverrà solo su una piccolissima percentuale dei suoi parametri (LoRA Adapters).

---

## 2. Il "Pensiero del Commercialista" (Instruction Tuning)

Il fine-tuning in questa fase serve per insegnare al modello *come* rispondere, non necessarimente *cosa* sapere a memoria (per quello hai già il tuo sistema RAG). Serve il cosiddetto **Instruction Tuning**.

Viene preparato un *Dataset* (es. 500-1000 domande/risposte) salvato in tre file JSONL: `train.jsonl` (addestramento) e `valid.jsonl` (verifica).

**Esempio di Formato MLX richiesto:**

```json
{"text": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nSei un Commercialista qualificato.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nHo aperto in regime forfettario. Come gestisco le spese dell'auto?<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\nEgregio Cliente, la risposta è negativa. Nel Regime Forfettario la determinazione del reddito avviene in via forfettaria (art 1 commi 54-89 L.190/2014)...<|eot_id|>"}
```

*(Nota: I token `<|start_header_id|>` dipendono dallo specifico modello scelto).*

---

## 3. Procedura Operativa 100% Mac (Step-by-Step)

### Fase A: Preparazione del Dataset

1. Usare i documenti Legali (Step 1 e 2).
2. Scrivere uno script Python che, tramite le API di un modello avanzato (es. GPT-4o), auto-generi centinaia di finti "Casi Studio cliente-commercialista".
3. Salvare tutto formattato ad-hoc nei file `data/train.jsonl` e `data/valid.jsonl`.
4. Revisionare le risposte a mano: lo stile appreso nel testo sarà replicato al 100% dal tuo modello finale.

### Fase B: Installazione Ambiente Apple MLX

Aprire il Terminale sul Mac e posizionarsi nella cartella `step6_finetuning`:

1. Creare un ambiente virtuale per MLX (consigliato per non sporcare il sistema):

    ```bash
    python3 -m venv mlx_env
    source mlx_env/bin/activate
    pip install mlx-lm datasets
    ```

2. Installare la libreria Apple MLX per fine-tuning:

    ```bash
    
    ```

### Fase C: Avvio del Fine-Tuning QLoRA (Il Calcolo Lungo)

L'addestramento vero e proprio avviene tramite un singolo comando da terminale, in cui MLX scarica il modello originale da HuggingFace, lo comprime al volo a 4-bit (QLoRA) e avvia il loop sulla tua GPU (7 Core).

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

* **`--model ...-4bit`:** Partiamo direttamente da un modello già preparato a 4-bit per saturare meno memoria all'avvio.
* **`--batch-size 1`:** Fondamentale per la tua macchina. Un batch size superiore a 1 crasherebbe la RAM da 8GB.
* **`--iters 400` / `--iters 1000`:** È il numero di cicli di apprendimento. **Portandolo a 400/500 velocizzerai considerevolmente il tempo di calcolo**, ed essendo il tuo dataset da circa 411 esempi per il training, 400 iterazioni sono circa "un'epoca intera" di osservazione (ovvero il modello guarda gli esempi quasi 1 volta ciascuno). Con `--iters 1000` farà più giri consolidando meglio, ma aumenterà i tempi. Ti suggeriamo di partire con `--iters 400` (o `--iters 500`) come primo esperimento.
* **Rallentamenti attesi e Temperature (MacBook Air):** Data la RAM limitata di 8GB, il disco fisso SSD scriverà continuamente (Swap memory). Essendo il MacBook Air M1 sprovvisto di ventole attive, la scocca in alluminio dissiperà passivamente il calore. C'è la concreta possibilità di "Thermal Throttling": quando il Mac si scalderà, abbasserà volontariamente le frequenze di calcolo per non fondere nulla. Le ore di calcolo stimate si dilateranno ulteriormente man mano che salirà la temperatura. Si raccomanda di tenerlo sollevato e areato.

### Fase D: Fusione dei Pesi (Dequantizzazione FP16)

A fine calcolo, MLX avrà generato una cartella `adapters/` contenente solo la "conoscenza specializzata" del commercialista nel formato LoRA.
Per poterla usare facilmente nell'ecosistema Ollama aggirando incompatibilità sui formati 4-bit proprietari, la tecnica migliore è fondere il modello decomprimendolo nel formato standard (FP16).

Sempre nel terminale di MLX, lancia:

```bash
mlx_lm.fuse \
  --model mlx-community/Llama-3.2-3B-Instruct-4bit \
  --adapter-path adapters \
  --dequantize \
  --save-path ./commercialista_mlx_fp16
```

Il Mac lavorerà per un paio di minuti sul disco SSD e genererà una nuova cartella `commercialista_mlx_fp16` da circa 6.5 GB con il modello unito e uncompressed.

### Fase E: Integrazione Auto-Quantizzata su Ollama

Ollama possiede uno strumento eccellente capace di importare intere cartelle salvate in formato FP16, ri-comprimendole chirurgicamente (e velocemente) in `.gguf` Q4 dietro le quinte.

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

In questo modo avrai svolto **tutta l'operazione in maniera del tutto offline, sicura e in locale sul tuo Mac M1**.
