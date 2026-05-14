import json
import os
import re
import glob
import concurrent.futures
import multiprocessing

# ---------------------------------------------------------------------------
# Dipendenze Avanzate (Grace-Blackwell)
# ---------------------------------------------------------------------------
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("ATTENZIONE: PyMuPDF (fitz) non installato.")

try:
    from langchain_experimental.text_splitter import SemanticChunker
    from langchain_huggingface import HuggingFaceEmbeddings
    import torch
    LANGCHAIN_SPLITTER_AVAILABLE = True
except ImportError:
    LANGCHAIN_SPLITTER_AVAILABLE = False
    print("ATTENZIONE: Dipendenze per Semantic Chunking non installate. Fallback su CPU/Basic.")

# ---------------------------------------------------------------------------
# Configurazione percorsi
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR  = os.path.join(SCRIPT_DIR, "../step1_download_laws/archivio_agenzia_entrate")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "accountant_rag_dataset")

# Determinazione Dinamica dell'Hardware (Blackwell GPU vs Grace CPU)
if LANGCHAIN_SPLITTER_AVAILABLE:
    # Se PyTorch rileva la GPU Blackwell (CUDA), userà quella, altrimenti scala sui 20 core Grace (CPU)
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
else:
    DEVICE = "cpu"

# Variabile globale usata dai worker del ProcessPool per evitare conflitti di contesto CUDA
global_splitter = None

def get_text_splitter():
    """Restituisce un SemanticChunker basato su intelligenza artificiale se disponibile."""
    if LANGCHAIN_SPLITTER_AVAILABLE:
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2", 
            model_kwargs={'device': DEVICE}
        )
        # Il SemanticChunker valuta il significato delle frasi per decidere dove tagliare
        return SemanticChunker(
            embeddings, breakpoint_threshold_type="percentile"
        )

    # Fallback minimale meccanico (nessuna intelligenza semantica)
    class _FallbackSplitter:
        def split_text(self, text):
            return [text[i:i+1500] for i in range(0, len(text), 1500)]
    return _FallbackSplitter()


def worker_init():
    """Inizializzatore per i processi worker. Crea una singola istanza del modello AI per core."""
    global global_splitter
    # Evita il caricamento dei log di HuggingFace da 20 processi simultanei
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    global_splitter = get_text_splitter()


# ===========================  ESTRAZIONE TESTO  ============================

def sanitize_text(text):
    """Rimuove i caratteri di controllo che rompono il parsing JSON strict."""
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

def extract_text_from_pdf(filepath):
    if not PYMUPDF_AVAILABLE:
        return ""
    try:
        doc = fitz.open(filepath)
        text = "".join(page.get_text("text") + "\n" for page in doc if page.get_text("text"))
        doc.close()
        return text
    except Exception as e:
        print(f"  [ERRORE] Lettura PDF fallita: {filepath} — {e}")
        return ""

def extract_metadata_from_path(filename, filepath):
    clean_name = filename.replace("+", " ")
    metadata = {
        "act_type":   "Documento Agenzia Entrate",
        "act_date":   "Unknown",
        "act_number": "Unknown",
        "full_title": clean_name,
        "urn":        filepath,
        "anno":       "Unknown",
    }
    lower = clean_name.lower()
    
    if "circolare" in lower: metadata["act_type"] = "Circolare"
    elif "provvedimento" in lower: metadata["act_type"] = "Provvedimento"
    elif "risoluzione" in lower: metadata["act_type"] = "Risoluzione"
    elif "risposta" in lower or "interpello" in lower: metadata["act_type"] = "Risposta Interpello"

    num_match = re.search(r'\bn\.?\s*(\d+)', clean_name, re.IGNORECASE)
    if num_match: metadata["act_number"] = num_match.group(1)

    year_match = re.search(r'(20\d{2})', clean_name)
    if year_match:
        metadata["anno"] = year_match.group(1)
        metadata["act_date"] = year_match.group(1)

    date_match = re.search(r'(\d{2})[\./]?(\d{2})[\./]?(20\d{2})', clean_name)
    if date_match:
        metadata["act_date"] = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}"

    return metadata

# ===========================  PIPELINE PRINCIPALE  =========================

def process_document(filepath):
    """Processa un singolo documento (estrazione parallela + semantic chunking parallelo)."""
    global global_splitter
    filename = os.path.basename(filepath)

    text = extract_text_from_pdf(filepath)
    if not text.strip():
        return []

    text = sanitize_text(text)
    metadata = extract_metadata_from_path(filename, filepath)

    # Chunking intelligente basato sulla GPU Blackwell (o fallback CPU)
    chunks_text = global_splitter.split_text(text)

    results = []
    for i, chunk_text in enumerate(chunks_text):
        header = f"Reference: {metadata['act_type']}"
        if metadata["act_number"] != "Unknown": header += f" N. {metadata['act_number']}"
        if metadata["anno"] != "Unknown": header += f" del {metadata['anno']}"
        header += f"\nFile: {filename}\nChunk: {i+1}/{len(chunks_text)}"

        results.append({
            "metadata": {
                **metadata,
                "chunk_id": str(i),
                "source_id": f"{metadata['act_type'].replace(' ', '_')}_{metadata['act_number']}_{metadata['anno']}_chunk_{i}"
            },
            "page_content": f"{header}\n\n{chunk_text.strip()}",
        })
    return results

def build_agenzia_rag_dataset():
    print("=" * 80)
    print("Preprocessing Agenzia delle Entrate (Acer Veriton High-Perf AI)")
    if LANGCHAIN_SPLITTER_AVAILABLE:
        print(f"Modalità: AI Semantic Chunking attivato (Dispositivo di calcolo: {DEVICE.upper()})")
    else:
        print("Modalità: Standard (Librerie AI non rilevate)")
    print("=" * 80)

    if not PYMUPDF_AVAILABLE:
        print("\n*** ERRORE: PyMuPDF è necessario. ***")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_files = sorted(glob.glob(os.path.join(INPUT_DIR, "**/*.pdf"), recursive=True))
    all_files += sorted(glob.glob(os.path.join(INPUT_DIR, "**/*.PDF"), recursive=True))
    unique_files = list(dict.fromkeys(all_files))

    if not unique_files:
        print(f"\nNessun file PDF trovato in: {INPUT_DIR}")
        return

    output_path = os.path.join(OUTPUT_DIR, "dataset_agenzia_langchain.jsonl")
    total_chunks = 0
    
    print(f"Avvio dell'elaborazione parallela e AI su {len(unique_files)} documenti...")
    print("Il caricamento dei modelli AI richiederà qualche secondo di inizializzazione...\n")

    # Utilizzo di 20 Core (CPU) con iniezione del modello AI (GPU/CPU) per ogni worker
    with open(output_path, "w", encoding="utf-8") as out_file:
        with concurrent.futures.ProcessPoolExecutor(initializer=worker_init) as executor:
            for i, chunks in enumerate(executor.map(process_document, unique_files)):
                if (i + 1) % 10 == 0 or (i + 1) == len(unique_files):
                    print(f"Progresso: completati {i+1}/{len(unique_files)} documenti...")
                
                total_chunks += len(chunks)
                for chunk in chunks:
                    out_file.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print("\n" + "=" * 80)
    print(f"Elaborazione AI Parallela completata!")
    print(f"  File letti:   {len(unique_files)}")
    print(f"  Chunk creati: {total_chunks} (Semanticamente strutturati)")
    print(f"  Output:       {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)
    build_agenzia_rag_dataset()
