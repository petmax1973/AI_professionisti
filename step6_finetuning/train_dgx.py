from trl import SFTTrainer
from transformers import TrainingArguments, BitsAndBytesConfig, AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset
import torch

# 1. Caricamento Dataset (es. JSONL)
# Assicurati di avere i file train.jsonl e valid.jsonl nella cartella data/
dataset = load_dataset("json", data_files={"train": "data/train.jsonl", "test": "data/valid.jsonl"})

# 2. Configurazione nativa per sfruttare i Tensor Core FP4 di Blackwell
quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="fp4", # Attiva il formato FP4 supportato in hardware
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16
)

base_model = "meta-llama/Llama-3.2-3B-Instruct"

print("Caricamento tokenizer e modello in FP4...")
tokenizer = AutoTokenizer.from_pretrained(base_model)
model = AutoModelForCausalLM.from_pretrained(
    base_model,
    quantization_config=quant_config,
    device_map="auto"
)

# 3. Parametri di Addestramento
args = TrainingArguments(
    output_dir="./outputs",
    per_device_train_batch_size=16, # L'efficienza dell'FP4 permette batch enormi
    gradient_accumulation_steps=2,
    learning_rate=2e-4,
    bf16=True, # I calcoli intermedi mantengono l'alta precisione (Brain Float 16)
    num_train_epochs=3,
    logging_steps=10
)

# 4. Inizializzazione SFTTrainer
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    args=args,
    # NOTA: qui potresti aggiungere la peft_config per LoRA
)

# 5. Avvio Training
print("Avvio del fine-tuning nativo in FP4 su DGX Blackwell...")
trainer.train()
