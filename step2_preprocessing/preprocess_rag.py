import json
import os
import glob
from pathlib import Path

# Source and destination directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "../step1_download_laws/documents_collection")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "accountant_rag_dataset")

def extract_law_metadata(data):
    """Extracts the main metadata of the law from the JSON."""
    heading = data.get('intestazione', {})
    metadata = data.get('metadati', {})
    
    return {
        "act_type": heading.get('tipoDoc', 'Unknown'),
        "act_date": metadata.get('dataDoc', 'Unknown'),
        "act_number": heading.get('numDoc', 'Unknown'),
        "full_title": heading.get('titoloDoc', '').strip(),
        "urn": metadata.get('urn', '')
    }

def extract_articles_recursive(elements, law_heading, extracted_articles):
    """
    Recursively navigates the 'elementi' tree of the articles or annexes
    to find and extract individual articles, paragraphs, or attachments.
    """
    for element in elements:
        nir_name = str(element.get('nomeNir', '')).lower()
        
        # We handle 'articolo' (article) but also 'allegato' (attachment)
        if nir_name in ['articolo', 'allegato']:
            element_number = str(element.get('numNir', str(element.get('idNir', ''))))
            rubric = element.get('rubricaNir', None)
            article_text = element.get('testo', '')
            art_notes = element.get('noteArt', '')
            
            # Extract Effective Dates (first version found)
            effective_start = "Unknown"
            vigore_versions = element.get('dataVigoreVersione', [])
            if vigore_versions and isinstance(vigore_versions, list) and len(vigore_versions) > 0:
                effective_start = vigore_versions[0].get('inizioVigore', 'Unknown')
            
            # Cleans up the text from leading and trailing backslash n
            if article_text:
                article_text = article_text.strip()
                
            # Combines the rubric (article title) with the text if it exists
            final_text = article_text or ""
            if rubric:
                final_text = f"Rubric: {rubric}\n\n{final_text}"
                
            # Add any explanatory Notes if they exist
            if art_notes and str(art_notes).strip() != "":
                final_text += f"\n\n--- EXPLANATORY NOTES FOR THE ARTICLE ---\n{str(art_notes).strip()}"
                
            # We create the final chunk with the injected metadata
            component_type = "Article" if nir_name == 'articolo' else "Attachment"
            
            chunk = {
                "metadata": {
                    # Transfer the parent law's metadata
                    **law_heading,
                    f"{nir_name}_num": element_number,
                    "effective_start": effective_start,
                    "source_id": f"{law_heading['act_type']}_{law_heading['anno']}_{law_heading['act_number']}_{component_type}_{element_number}"
                },
                "page_content": f"Reference: {law_heading['act_type']} number {law_heading['act_number']} of the {law_heading['act_date']}\n{component_type}: {element_number}\nValidity starting from: {effective_start}\n\n{final_text}"
            }
            
            extracted_articles.append(chunk)
            
        # Recursion: explore sub-elements (e.g. paragraphs, letters, if present nested)
        sub_elements = element.get('elementi', [])
        if sub_elements:
            extract_articles_recursive(sub_elements, law_heading, extracted_articles)

def process_json_file(filepath):
    """Processes a single JSON file and returns the list of its articles (chunks)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"JSON parsing error in file: {filepath}")
            return []

    # 1. Retrieve global metadata of the law
    law_metadata = extract_law_metadata(data)
    
    # Adding the year extracted from the date for convenience
    law_metadata['anno'] = law_metadata['act_date'].split('-')[0] if '-' in law_metadata['act_date'] else 'Unknown'

    extracted_articles = []
    
    # 2. Exploration of the articles (Articles and Paragraphs)
    articles_data = data.get('articolato', {})
    root_elements = articles_data.get('elementi', [])
    if root_elements:
         extract_articles_recursive(root_elements, law_metadata, extracted_articles)
         
    # 3. Exploration of Annexes (Attachments, where the core of the law often is)
    annexes = data.get('annessi', {})
    if_annexes_root = annexes.get('elementi', [])
    if if_annexes_root:
         extract_articles_recursive(if_annexes_root, law_metadata, extracted_articles)
         
    return extracted_articles

def build_rag_dataset():
    print("Beginning processing of dataset for streaming RAG (JSONL)...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Recursive search to support potential subdirectories (e.g. "decrees", "laws")
    all_files = glob.glob(os.path.join(INPUT_DIR, "**/*.json"), recursive=True)
    total_articles = 0
    output_path = os.path.join(OUTPUT_DIR, "dataset_rag_langchain.jsonl")
    
    # We open the final file in append/log mode
    with open(output_path, 'w', encoding='utf-8') as out_file:
        for index, filepath in enumerate(all_files):
            filename = os.path.basename(filepath)
            print(f"[{index+1}/{len(all_files)}] Processing: {filename}...")
            
            articles = process_json_file(filepath)
            total_articles += len(articles)
            
            # We immediately write each chunk to disk as JSONL
            for article_chunk in articles:
                # json.dumps converts the dictionary into a compact JSON string (a single line)
                json_row = json.dumps(article_chunk, ensure_ascii=False)
                out_file.write(json_row + "\n")
                
    print(f"\nProcessing completed in streaming mode.")
    print(f"Read {len(all_files)} law files directly and generated {total_articles} total chunks.")
    print(f"Final dataset (JSON Lines - Scalable) saved in: {output_path}")

if __name__ == "__main__":
    build_rag_dataset()
