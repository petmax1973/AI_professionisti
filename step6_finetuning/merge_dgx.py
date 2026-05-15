from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

base_model = "Qwen/Qwen2.5-32B-Instruct" # Modello di partenza usato
adapter_dir = "./outputs"
save_dir = "./commercialista_blackwell_merged"

print("Caricamento del modello base in bf16...")
model = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype=torch.bfloat16, device_map="cuda")
tokenizer = AutoTokenizer.from_pretrained(base_model)

print("Unione dei pesi del Commercialista in corso...")
model = PeftModel.from_pretrained(model, adapter_dir)
model = model.merge_and_unload()

print("Salvataggio del modello finale...")
model.save_pretrained(save_dir, safe_serialization=True)
tokenizer.save_pretrained(save_dir)
print("Merge completato con successo!")
