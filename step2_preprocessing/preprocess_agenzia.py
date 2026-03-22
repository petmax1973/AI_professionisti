import json
import os
import re
import glob

# ---------------------------------------------------------------------------
# Dipendenze opzionali (con fallback graceful)
# ---------------------------------------------------------------------------
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("ATTENZIONE: PyMuPDF (fitz) non installato. Esegui: pip install PyMuPDF")

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    LANGCHAIN_SPLITTER_AVAILABLE = True
except ImportError:
    LANGCHAIN_SPLITTER_AVAILABLE = False
    print("ATTENZIONE: langchain-text-splitters non installato. Esegui: pip install langchain-text-splitters")


# ---------------------------------------------------------------------------
# Configurazione percorsi
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR  = os.path.join(SCRIPT_DIR, "../step1_download_laws/archivio_agenzia_entrate")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "accountant_rag_dataset")

# Parametri di chunking
CHUNK_SIZE    = 1500
CHUNK_OVERLAP = 150


# ===========================  UTILITA  =====================================

def get_text_splitter():
    """Restituisce uno splitter LangChain se disponibile, altrimenti un fallback."""
    if LANGCHAIN_SPLITTER_AVAILABLE:
        return RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            is_separator_regex=False,
        )

    # Fallback minimale (nessuna dipendenza esterna)
    class _FallbackSplitter:
        def split_text(self, text):
            chunks = []
            start = 0
            while start < len(text):
                end = start + CHUNK_SIZE
                chunks.append(text[start:end])
                start = end - CHUNK_OVERLAP
            return chunks
    return _FallbackSplitter()


# ===========================  ESTRAZIONE TESTO  ============================

def sanitize_text(text):
    """Rimuove i caratteri di controllo (form-feed, NUL, vertical-tab ecc.)
    che rompono il parsing JSON strict. Preserva newline e tab."""
    import re
    # Rimuove tutti i caratteri di controllo C0 tranne \n (0x0A) e \t (0x09)
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

def extract_text_from_pdf(filepath):
    """Estrae il testo da un file PDF con PyMuPDF."""
    if not PYMUPDF_AVAILABLE:
        print(f"  [SKIP] PyMuPDF non disponibile, impossibile leggere: {filepath}")
        return ""
    try:
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            page_text = page.get_text("text")
            if page_text:
                text += page_text + "\n"
        doc.close()
        return text
    except Exception as e:
        print(f"  [ERRORE] Lettura PDF fallita: {filepath} — {e}")
        return ""


def extract_text_from_file(filepath):
    """Dispatcher: sceglie l'estrattore corretto in base all'estensione."""
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(filepath)
    # Estensioni future: .doc, .docx, .xls, .xlsx
    # elif ext in ('.doc', '.docx'):
    #     return extract_text_from_docx(filepath)
    else:
        print(f"  [SKIP] Estensione non gestita: {ext} — {os.path.basename(filepath)}")
        return ""


# ===========================  METADATI  ====================================

def extract_metadata_from_path(filename, filepath):
    """
    Ricostruisce i metadati (tipo, numero, anno) dal nome del file e dal path.
    Esempio: Circolare+n+7+del+9+aprile+2019_Circolare+N.+7_09042019.pdf
    """
    # Decodifica gli spazi codificati come '+'
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

    # --- Tipo atto ---
    if "circolare" in lower:
        metadata["act_type"] = "Circolare"
    elif "provvedimento" in lower:
        metadata["act_type"] = "Provvedimento"
    elif "risoluzione" in lower:
        metadata["act_type"] = "Risoluzione"
    elif "risposta" in lower or "interpello" in lower:
        metadata["act_type"] = "Risposta Interpello"

    # --- Numero atto (pattern: "n 7", "n. 7", "n_7" ecc.) ---
    num_match = re.search(r'\bn\.?\s*(\d+)', clean_name, re.IGNORECASE)
    if num_match:
        metadata["act_number"] = num_match.group(1)

    # --- Anno (4 cifre) ---
    year_match = re.search(r'(20\d{2})', clean_name)
    if year_match:
        metadata["anno"] = year_match.group(1)
        metadata["act_date"] = year_match.group(1)

    # Prova a estrarre una data più precisa (dd/mm/yyyy o ddmmyyyy)
    date_match = re.search(r'(\d{2})[\./]?(\d{2})[\./]?(20\d{2})', clean_name)
    if date_match:
        metadata["act_date"] = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}"

    return metadata


# ===========================  PIPELINE PRINCIPALE  =========================

def process_document(filepath, text_splitter):
    """Processa un singolo documento e ritorna la lista di chunk pronti per JSONL."""
    filename = os.path.basename(filepath)

    text = extract_text_from_file(filepath)
    if not text.strip():
        return []

    # Rimuove caratteri di controllo che rompono il JSON
    text = sanitize_text(text)

    metadata = extract_metadata_from_path(filename, filepath)

    chunks_text = text_splitter.split_text(text)

    results = []
    for i, chunk_text in enumerate(chunks_text):
        # Testata iniettata nel page_content (come fa preprocess_rag.py)
        header = f"Reference: {metadata['act_type']}"
        if metadata["act_number"] != "Unknown":
            header += f" N. {metadata['act_number']}"
        if metadata["anno"] != "Unknown":
            header += f" del {metadata['anno']}"
        header += f"\nFile: {filename}"
        header += f"\nChunk: {i+1}/{len(chunks_text)}"

        page_content = f"{header}\n\n{chunk_text.strip()}"

        chunk = {
            "metadata": {
                **metadata,
                "chunk_id": str(i),
                "source_id": (
                    f"{metadata['act_type'].replace(' ', '_')}"
                    f"_{metadata['act_number']}"
                    f"_{metadata['anno']}"
                    f"_chunk_{i}"
                ),
            },
            "page_content": page_content,
        }
        results.append(chunk)

    return results


def build_agenzia_rag_dataset():
    print("=" * 70)
    print("Preprocessing documenti Agenzia delle Entrate → JSONL per il RAG")
    print("=" * 70)

    if not PYMUPDF_AVAILABLE:
        print("\n*** ERRORE: PyMuPDF è necessario. Installalo con: pip install PyMuPDF ***")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Ricerca ricorsiva di tutti i PDF
    all_files = sorted(glob.glob(os.path.join(INPUT_DIR, "**/*.pdf"), recursive=True))
    # Aggiungi anche eventuali .PDF (case-insensitive su filesystem case-sensitive)
    all_files += sorted(glob.glob(os.path.join(INPUT_DIR, "**/*.PDF"), recursive=True))
    # Rimuovi duplicati mantenendo l'ordine
    seen = set()
    unique_files = []
    for f in all_files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)
    all_files = unique_files

    if not all_files:
        print(f"\nNessun file PDF trovato in: {INPUT_DIR}")
        return

    print(f"Trovati {len(all_files)} file PDF da elaborare.\n")

    text_splitter = get_text_splitter()
    total_chunks = 0
    output_path = os.path.join(OUTPUT_DIR, "dataset_agenzia_langchain.jsonl")

    with open(output_path, "w", encoding="utf-8") as out_file:
        for index, filepath in enumerate(all_files):
            filename = os.path.basename(filepath)
            print(f"[{index + 1}/{len(all_files)}] {filename} ...", end=" ")

            chunks = process_document(filepath, text_splitter)
            total_chunks += len(chunks)

            for chunk in chunks:
                json_row = json.dumps(chunk, ensure_ascii=False)
                out_file.write(json_row + "\n")

            print(f"→ {len(chunks)} chunk")

    print("\n" + "=" * 70)
    print(f"Elaborazione completata.")
    print(f"  File letti:   {len(all_files)}")
    print(f"  Chunk creati: {total_chunks}")
    print(f"  Output:       {output_path}")
    print("=" * 70)


if __name__ == "__main__":
    build_agenzia_rag_dataset()
