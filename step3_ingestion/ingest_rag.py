import os
import json
import torch

# Disabilita completamente la telemetria di ChromaDB per rispetto della Privacy e del GDPR
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Path configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# The jsonl file created in step 2
DATASET_PATH = os.path.join(SCRIPT_DIR, "../step2_preprocessing/accountant_rag_dataset/dataset_rag_langchain.jsonl")
# Where we will save the vector database
CHROMA_DB_DIR = os.path.join(SCRIPT_DIR, "laws_vector_db")

# Free and open-source model with excellent performance in Italian
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-base"

def iter_jsonl_documents(filepath, skip: int = 0):
    print(f"Loading data from JSONL file in streaming mode: {filepath} ...")
    if skip > 0:
        print(f"Skipping the first {skip} documents...")
        
    # We use a custom generator reading the file line by line
    # to avoid RAM bottlenecks on huge jsonl files.
    from langchain.schema import Document
    
    skipped_count = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
                
            if skipped_count < skip:
                skipped_count += 1
                continue
                
            data = json.loads(line)
            
            text = data.get("page_content", "")
            metadata = data.get("metadata", {})
            
            doc = Document(page_content=text, metadata=metadata)
            yield doc

def populate_vector_db():
    print("Initializing the local Embedding model (may require downloading the first time)...")
    
    # Initialize the embeddings model
    # The parameter model_kwargs={'device': 'cpu'} (or 'mps' if on Mac Silicon M1/M2/M3)
    # mps uses Apple's dedicated GPU acceleration.
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'mps'}, # Change to 'cpu' if mps is not supported
            encode_kwargs={'batch_size': 16}
        )
    except Exception as e:
        print(f"Warning: Initialization on mps failed. Fallback to CPU. Error: {e}")
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'cpu'}
        )

    print(f"Creating the Chroma Vector Database in: {CHROMA_DB_DIR} ...")
    print("This process vectorizes each document (compute-intensive). It may take minutes or hours depending on the data...")
    
    # Create and persist the database
    # We process the generator in batches to avoid bottlenecks or memory issues
    batch_size = 100
    db = None
    total_processed = 0
    
    # Check if a database already exists to resume ingestion
    if os.path.exists(CHROMA_DB_DIR) and os.listdir(CHROMA_DB_DIR):
        print(f"Found existing database in {CHROMA_DB_DIR}. Resuming...")
        try:
            db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
            total_processed = db._collection.count()
            print(f"The database already contains {total_processed} documents.")
        except Exception as e:
            print(f"Error checking existing document count: {e}. Starting fresh.")
            db = None
            total_processed = 0
            
    document_iterator = iter_jsonl_documents(DATASET_PATH, skip=total_processed)
    batch = []
    
    for doc in document_iterator:
        batch.append(doc)
        if len(batch) >= batch_size:
            print(f"  -> Inserting batch of {len(batch)} documents (Total processed: {total_processed + len(batch)})...")
            if db is None:
                db = Chroma.from_documents(
                    documents=batch,
                    embedding=embeddings,
                    persist_directory=CHROMA_DB_DIR
                )
            else:
                db.add_documents(batch)
            total_processed += len(batch)
            batch = [] # Free RAM
            
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
            
    # Process any remaining documents smaller than a full batch
    if batch:
        print(f"  -> Inserting final batch of {len(batch)} documents (Total processed: {total_processed + len(batch)})...")
        if db is None:
            db = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=CHROMA_DB_DIR
            )
        else:
            db.add_documents(batch)
        total_processed += len(batch)
            
    print(f"\nCompleted! The local vector database is ready and saved to disk. Total embedded chunks: {total_processed}")
    
if __name__ == "__main__":
    populate_vector_db()
