import json
import os
import random

# Percorsi dei file
SOURCE_DATASET = "../step2_preprocessing/accountant_rag_dataset/dataset_rag_langchain.jsonl"
OUTPUT_DIR = "data"
TRAIN_FILE = os.path.join(OUTPUT_DIR, "train.jsonl")
VALID_FILE = os.path.join(OUTPUT_DIR, "valid.jsonl")

# Prompt di sistema per Llama-3 (ChatML/Llama3 Instruct format supportato da MLX)
SYSTEM_PROMPT = "Sei un Commercialista e Revisore Contabile italiano altamente qualificato. Le tue risposte devono essere sempre formali, oggettive, precise e citare scrupolosamente le normative di riferimento come richiesto dalla deontologia professionale."

# Template Domande (per variare sintassi)
QUESTION_TEMPLATES = [
    "Egregio Dottore, potrebbe chiarirmi cosa prevede l'Articolo {art} del {act_type} n. {num} in materia di '{rubric}'?",
    "Buongiorno, mi trovo a dover applicare il {act_type} {num} del {anno}. In particolare, cosa dispone l'art. {art} in termini di {rubric}?",
    "Salve. Desidero un parere professionale: quali sono le disposizioni normative dettate dall'Art. {art} ({rubric}) del {act_type} n. {num} ({anno})?",
    "Dottore, potrei avere un inquadramento normativo circa l'Articolo {art} del {act_type} {num} del {anno} relativo a '{rubric}'?",
    "Ho bisogno di una consulenza tecnica. Potrebbe spiegarmi il dettato dell'Art. {art} del {act_type} numero {num} ({anno}), intitolato '{rubric}'?"
]

# Template Risposte
ANSWER_TEMPLATES = [
    "Egregio Cliente, in riferimento al Suo quesito, il quadro normativo è molto chiaro.\n\nAi sensi dell'Articolo {art} del {act_type} numero {num} promulgato nell'anno {anno} (con entrata in vigore dal {date}), in materia di \"{rubric}\", il legislatore stabilisce testualmente quanto segue:\n\n{content}\n\nRimanendo a disposizione per qualsiasi ulteriore approfondimento, porgo cordiali saluti.",
    "Gentile Cliente, procedo a fornirLe il parere richiesto analizzando le fonti del diritto in vigore.\n\nFacendo esplicito riferimento al {act_type} n. {num} del {anno}, l'Art. {art} (Rubrica: {rubric}), entrato in vigore il {date}, dispone testualmente:\n\n{content}\n\nResto in attesa di un Suo riscontro per valutare le azioni conseguenti. Distinti saluti.",
    "In relazione alla problematica da Lei esposta, è dirimente analizzare la norma di riferimento.\n\nIl {act_type} {num} del {anno}, nello specifico all'Articolo {art} - recante \"{rubric}\" - prevede quanto segue (con decorrenza {date}):\n\n{content}\n\nSpero che questa delucidazione tecnica Le sia di ausilio pratico. Cordialmente.",
    "Egregio, in merito alla questione sollevata relativa a \"{rubric}\", La informo che la disciplina di riferimento è reperibile nell'Articolo {art} del {act_type} n. {num}/{anno}.\n\nDal {date}, la normativa regolamenta la casistica come segue:\n\n{content}\n\nResto a disposizione per eventuali chiarimenti applicativi in merito. Saluti professionali."
]

def format_mlx_llama3(prompt_system, user_content, assistant_content):
    """Formatta la conversazione nel template di Llama 3 per MLX"""
    return {
        "text": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{prompt_system}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_content}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{assistant_content}<|eot_id|>"
    }

def generate_dataset(num_examples=1000):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(SOURCE_DATASET):
        print(f"Errore: File sorgente non trovato {SOURCE_DATASET}")
        return

    dataset = []
    
    with open(SOURCE_DATASET, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if len(dataset) >= num_examples:
                break
                
            try:
                doc = json.loads(line)
                meta = doc.get("metadata", {})
                content = doc.get("page_content", "").strip()
                
                # Pulisci il contenuto dal preambolo inutile per non raddoppiare l'info
                if "Rubric:" in content:
                    content = content.split("Rubric:")[1].split("\n", 1)[1].strip()
                    content = content.split("--- EXPLANATORY NOTES")[0].strip() # rimuovi le note per essere coinciso e professionale

                if not content or len(content) < 50:
                    continue

                act_type = meta.get("act_type", "Provvedimento").title()
                num = meta.get("act_number", "N.D.")
                anno = meta.get("anno", "N.D.")
                art = meta.get("articolo_num", "N.D.")
                date = meta.get("effective_start", "N.D.")
                
                # Estrai la rubrica dal titolo lungo se presente, altrimenti stringa generica
                full_title = meta.get("full_title", "")
                rubric = "Disposizioni normative"
                if len(full_title) > 0:
                    rubric_end = full_title.find(".")
                    if rubric_end > 0:
                        rubric = full_title[:rubric_end]
                    else:
                        rubric = full_title[:100] + "..."

                # Scegli template random
                q_template = random.choice(QUESTION_TEMPLATES)
                a_template = random.choice(ANSWER_TEMPLATES)
                
                question = q_template.format(art=art, act_type=act_type, num=num, rubric=rubric, anno=anno)
                answer = a_template.format(art=art, act_type=act_type, num=num, anno=anno, date=date, rubric=rubric, content=content)
                
                # Formatta e appendi
                formatted_doc = format_mlx_llama3(SYSTEM_PROMPT, question, answer)
                dataset.append(formatted_doc)
                
            except json.JSONDecodeError:
                continue
                
    # Shuffle del dataset
    random.shuffle(dataset)
    
    # Split 90% Train, 10% Valid
    split_index = int(len(dataset) * 0.9)
    train_data = dataset[:split_index]
    valid_data = dataset[split_index:]
    
    # Salva
    with open(TRAIN_FILE, 'w', encoding='utf-8') as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
    with open(VALID_FILE, 'w', encoding='utf-8') as f:
        for item in valid_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
    print(f"Dataset Generato con Successo!")
    print(f"- Totali Esempi: {len(dataset)}")
    print(f"- Train File: {TRAIN_FILE} ({len(train_data)} esempi)")
    print(f"- Valid File: {VALID_FILE} ({len(valid_data)} esempi)")

if __name__ == "__main__":
    generate_dataset(1000)
