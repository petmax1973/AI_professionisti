import os
import time
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../step3_ingestion/laws_vector_db")
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-base"

print("Loading embeddings...")
t0 = time.time()
try:
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'}
    )
    print("Using CPU...")
    pass
except Exception:
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'}
    )
    print("Using CPU...")
print(f"Embeddings loaded in {time.time()-t0:.2f}s")

print("Loading ChromaDB...")
t0 = time.time()
db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
print(f"ChromaDB loaded in {time.time()-t0:.2f}s. Elements: {db._collection.count()}")

print("Querying ChromaDB...")
t0 = time.time()
docs = db.similarity_search("tasse e tributi", k=2)
print(f"Query completed in {time.time()-t0:.2f}s")
for i, d in enumerate(docs):
    print(f"Result {i+1} source: {d.metadata.get('source_id', 'unknown')}")
print("Vector DB OK.")
