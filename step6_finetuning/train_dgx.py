import os
import torch
from trl import SFTTrainer, SFTConfig
from transformers import BitsAndBytesConfig, AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset
from peft import LoraConfig

# ============================================================================
# train_dgx.py — QLoRA Fine-Tuning su Acer Veriton VN100 GB10 Blackwell
# ============================================================================
# NOTA: Il GB10 ha 128 GB di memoria UNIFICATA (condivisa CPU/GPU).
# I parametri sono calibrati per non saturare la RAM e bloccare il sistema.
# ============================================================================

# Safeguard: limita l'allocazione CUDA per proteggere il sistema operativo
# Lascia ~28 GB liberi per OS, kernel e processi di sistema
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

print("=" * 60)
print("QLoRA Fine-Tuning — Acer Veriton VN100 GB10 Blackwell")
print("=" * 60)

# 1. Caricamento Dataset (JSONL)
# Assicurati di avere i file train.jsonl e valid.jsonl nella cartella data/
print("\n[1/5] Caricamento dataset...")
dataset = load_dataset("json", data_files={"train": "data/train.jsonl", "test": "data/valid.jsonl"})
print(f"  Train: {len(dataset['train'])} campioni | Valid: {len(dataset['test'])} campioni")

# 2. Configurazione QLoRA — Quantizzazione FP4 nativa Blackwell
print("\n[2/5] Configurazione quantizzazione FP4...")
quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="fp4",            # Formato FP4 supportato in hardware dai Tensor Core Blackwell
    bnb_4bit_use_double_quant=True,       # Doppia quantizzazione per risparmiare ulteriore memoria
    bnb_4bit_compute_dtype=torch.bfloat16 # Calcoli intermedi in BF16 per precisione
)

base_model = "Qwen/Qwen2.5-32B-Instruct"

print(f"\n[3/5] Caricamento modello {base_model} in FP4...")
print("  (può richiedere alcuni minuti al primo avvio)")
tokenizer = AutoTokenizer.from_pretrained(base_model)

# Imposta pad_token se non presente (necessario per il training)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    base_model,
    quantization_config=quant_config,
    device_map="auto",
    max_memory={0: "100GiB"},  # Limita a 100 GB, lascia ~28 GB per il sistema
    dtype=torch.bfloat16,
)

# Stampa utilizzo memoria dopo il caricamento del modello
mem_allocated = torch.cuda.memory_allocated() / (1024**3)
mem_reserved = torch.cuda.memory_reserved() / (1024**3)
print(f"  Memoria GPU allocata: {mem_allocated:.1f} GB")
print(f"  Memoria GPU riservata: {mem_reserved:.1f} GB")

# 3. Parametri di Addestramento — Calibrati per memoria unificata 128 GB
print("\n[4/5] Configurazione training...")
args = SFTConfig(
    output_dir="./outputs",
    per_device_train_batch_size=1,         # Batch size conservativo per memoria unificata
    gradient_accumulation_steps=8,         # Effective batch size = 8 (compensa il batch piccolo)
    learning_rate=2e-4,
    bf16=True,                             # Calcoli in BF16 sui Tensor Core Blackwell
    num_train_epochs=3,
    logging_steps=10,
    save_steps=100,
    save_total_limit=2,                    # Mantiene solo i 2 checkpoint più recenti
    gradient_checkpointing=True,           # CRITICO: scambia tempo per memoria (~60% meno RAM)
    gradient_checkpointing_kwargs={"use_reentrant": False},
    optim="adamw_8bit",                    # Optimizer a 8-bit: dimezza la memoria dell'optimizer
    dataloader_num_workers=0,              # Evita worker multipli che duplicano dati in memoria
    warmup_steps=10,                       # ~3% di warmup (≈337 step totali)
    weight_decay=0.01,
    report_to="none",                      # Disabilita logging esterno (wandb, etc.)
    max_grad_norm=0.3,                     # Gradient clipping per stabilità
    max_length=1024,                       # CRITICO: limita sequenze (max nel dataset = 57K token!)
    dataset_text_field="text",             # Campo del JSONL contenente il testo
)

# Configurazione LoRA (Adapter) — identica all'originale
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

# 4. Inizializzazione SFTTrainer
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    args=args,
    peft_config=peft_config,
    processing_class=tokenizer,
)

# 5. Avvio Training
print("\n[5/5] Avvio QLoRA fine-tuning in FP4 su GB10 Blackwell...")
print(f"  Batch size effettivo: {args.per_device_train_batch_size * args.gradient_accumulation_steps}")
print(f"  Max sequenza: 1024 token")
print(f"  Epoche: {args.num_train_epochs}")
print(f"  Gradient checkpointing: attivo")
print(f"  Optimizer: AdamW 8-bit")
print("-" * 60)

trainer.train()

# Salvataggio adapter LoRA finale
print("\n✅ Training completato!")
print("Salvataggio adapter LoRA in ./outputs/final_adapter...")
trainer.save_model("./outputs/final_adapter")
tokenizer.save_pretrained("./outputs/final_adapter")
print("Fatto! Per il merge, esegui: python merge_dgx.py")
