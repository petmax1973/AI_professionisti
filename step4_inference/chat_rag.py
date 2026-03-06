import os
import sys

# Disabilita completamente la telemetria di ChromaDB per rispetto della Privacy e del GDPR
os.environ["ANONYMIZED_TELEMETRY"] = "False"
# Suppress parallelism warnings from Huggingface Tokenizers
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# =========================
# PARAMETER CONFIGURATION
# =========================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: we use the exact same vector DB populated in step 3
CHROMA_DB_DIR = os.path.join(SCRIPT_DIR, "../step3_ingestion/laws_vector_db")

EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-base"
LLM_MODEL_NAME = "llama3"
RETRIEVER_K = 4 # Number of law chunks to inject into the LLM logic

def main():
    print("\n======================================================")
    print(" Avvio Assistente Legale AI - M1 Ottimizzato in corso ")
    print("======================================================\n")
    
    # 1. Verification of DB existence
    if not os.path.exists(CHROMA_DB_DIR):
        print(f"Errore: Il database vettoriale non esiste in {CHROMA_DB_DIR}")
        print("Assicurati di aver completato lo Step 3 (Ingestion) in precedenza.")
        sys.exit(1)

    print("Caricamento del modello linguistico Semantico (Embedding)...")
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'mps'}
        )
    except Exception:
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'cpu'}
        )
        
    print("Connessione al database vettoriale locale ChromaDB...")
    db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
    retriever = db.as_retriever(search_kwargs={"k": RETRIEVER_K})
    
    print(f"Connessione al modello LLM locale Ollama ({LLM_MODEL_NAME})...")
    llm = Ollama(model=LLM_MODEL_NAME)
    
    # 2. RAG Prompt Construction
    prompt_template = """Sei un severo e precisissimo assistente legale italiano, progettato per affiancare i commercialisti.
Devi rispondere alla domanda dell'utente utilizzando ESCLUSIVAMENTE il seguente contesto normativo estratto dalle banche dati ufficiali.
REGOLA FONDAMENTALE 1: Non usare alcuna conoscenza esterna al contesto. Non inventare date, numeri o articoli di legge.
REGOLA FONDAMENTALE 2: Se la risposta non è contenuta nei documenti del contesto, devi dire ESATTAMENTE: "Mi dispiace, ma non ho trovato informazioni sufficienti nei documenti a mia disposizione per rispondere a questa domanda."
REGOLA FONDAMENTALE 3: Cita sempre all'interno della tua spiegazione i riferimenti legislativi e/o l'articolo esatto su cui basi la risposta (li trovi nell'intestazione di ogni blocco del contesto).

CONTESTO NORMATIVO ORIGINALE ESTRATTO DAL DATABASE:
---------------------
{context}
---------------------

DOMANDA DEL PROFESSIONISTA: {question}

RISPOSTA DETTAGLIATA:"""

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )
    
    # 3. Chain Building
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )
    
    print("\n" + "="*54)
    print("  SISTEMA PRONTO. Inserisci la tua ricerca legale.  ")
    print("  (Scrivi 'esci', 'quit' o 'exit' per terminare)    ")
    print("======================================================\n")
    
    # 4. Interactive loop
    while True:
        try:
            query = input("\n👉 Domanda: ")
            
            if query.lower().strip() in ['esci', 'quit', 'exit']:
                print("\nChiusura Assistente Legale. A presto!")
                break
                
            if not query.strip():
                continue
                
            print("\n⏳ Ricerca nel Database e Generazione Risposta in corso...")
            
            # Execution
            result = qa_chain.invoke({"query": query})
            
            print("\n" + "-"*50)
            print("⚖️  RISPOSTA DELL'IA:")
            print("-"*50)
            print(result['result'])
            print("\n" + "-"*50)
            
            print("📑 FONTI NORMATIVE CONSULTATE:")
            # We want to print unique sources since sometimes consecutive chunks share the same source parent document
            sources_list = []
            for doc in result['source_documents']:
                source_id = doc.metadata.get('source_id', 'Sconosciuta')
                if source_id not in sources_list:
                    sources_list.append(source_id)
            
            for i, source in enumerate(sources_list):
                print(f"  [{i+1}] {source}")
                
        except KeyboardInterrupt:
            print("\n\nChiusura Assistente interrotta dall'utente. A presto!")
            break
        except Exception as e:
            print(f"\n❌ Errore critico durante l'interrogazione: {e}")
            print("Assicurati di avere l'app Ollama accesa e che il modello scaricato in background non abbia crashato.")

if __name__ == "__main__":
    main()
