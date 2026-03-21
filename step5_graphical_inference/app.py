import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
warnings.filterwarnings("ignore", message=".*urllib3.*")
warnings.filterwarnings("ignore", category=UserWarning, message=".*urllib3.*")
if hasattr(warnings, 'DependencyWarning'):
    warnings.filterwarnings("ignore", category=DependencyWarning, module="requests")
try:
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    warnings.simplefilter('ignore', InsecureRequestWarning)
except Exception:
    pass

import os
import sys

# Previene l'errore di torch.classes disabilitando il file watcher di Streamlit per questo script
os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"

import streamlit as st
import psutil

try:
    import torch
except ImportError:
    torch = None

st.set_page_config(
    page_title="Assistente Commercialista AI",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Disabilita completamente la telemetria di ChromaDB per rispetto della Privacy e del GDPR
os.environ["ANONYMIZED_TELEMETRY"] = "False"
# Suppress parallelism warnings from Huggingface Tokenizers
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM as Ollama

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
warnings.filterwarnings("ignore", message=".*urllib3.*")
# from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA

import tempfile
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, UnstructuredExcelLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# =========================
# PARAMETER CONFIGURATION
# =========================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: we use the exact same vector DB populated in step 3
CHROMA_DB_DIR = os.path.join(SCRIPT_DIR, "../step3_ingestion/laws_vector_db")

EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-base"
LLM_MODEL_NAME = "llama3:latest"
# LLM_MODEL_NAME = "test_mlx_import2:latest"
# LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
RETRIEVER_K = 4 # Number of law chunks to inject into the LLM logic

# =========================
# STREAMLIT CONFIGURATION
# =========================

st.title("⚖️ Assistente Commercialista AI")
st.markdown("Interroga la banca dati legislativa in linguaggio naturale. Nessun dato esce dal tuo Mac.")

# =========================
# INITIALIZATION (Cached)
# =========================
@st.cache_resource(show_spinner="Caricamento modelli in corso...")
def init_rag_system():
    # 1. Verification of DB existence
    if not os.path.exists(CHROMA_DB_DIR):
        st.error(f"Errore: Il database vettoriale non esiste in `{CHROMA_DB_DIR}`")
        st.info("Assicurati di aver completato lo Step 3 (Ingestion) in precedenza.")
        st.stop()

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
        
    db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
    retriever = db.as_retriever(search_kwargs={"k": RETRIEVER_K})
    
    llm = Ollama(model=LLM_MODEL_NAME, temperature=0.0)
    # llm = ChatOpenAI(
    #     base_url=LM_STUDIO_BASE_URL,
    #     api_key="lm-studio",  # Chiave fittizia per LM Studio
    #     model=LLM_MODEL_NAME,
    #     temperature=0.0
    # )
    
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
    
    # Main laws retriever exposed for hybrid use
    return qa_chain, retriever, embeddings, llm

qa_chain_laws, laws_retriever, embeddings, llm = init_rag_system()

# =========================
# DOCUMENT PROCESSING LOGIC
# =========================
def process_uploaded_files(uploaded_files, embeddings):
    documents = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for uploaded_file in uploaded_files:
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext == ".pdf":
                loader = PyPDFLoader(temp_path)
            elif ext == ".csv":
                loader = CSVLoader(temp_path)
            elif ext == ".xlsx":
                try:
                    loader = UnstructuredExcelLoader(temp_path)
                except Exception as e:
                    st.error(f"Errore caricamento Excel: {e}")
                    continue
            elif ext == ".txt":
                loader = TextLoader(temp_path)
            else:
                st.warning(f"Formato non supportato: {ext}")
                continue
                
            try:
                docs = loader.load()
                for doc in docs:
                    doc.metadata['source_id'] = uploaded_file.name
                documents.extend(docs)
            except Exception as e:
                st.error(f"Errore durante la lettura di {uploaded_file.name}: {e}")
                
    if not documents:
        return None
        
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)
    
    temp_vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
    return temp_vectorstore

doc_prompt_template = """Sei un assistente analitico esperto.
Rispondi alla domanda usando ESCLUSIVAMENTE le informazioni contenute nei documenti forniti.
Se la risposta non è presente, rispondi: "Non ci sono informazioni sufficienti nei documenti per rispondere."
Non inventare numeri, calcoli o dati che non siano esplicitamente scritti o calcolabili con esattezza dai documenti forniti.

DOCUMENTI CARICATI:
---------------------
{context}
---------------------

DOMANDA: {question}

RISPOSTA:"""

doc_prompt = PromptTemplate(template=doc_prompt_template, input_variables=["context", "question"])

hybrid_prompt_template = """Sei un eccellente assistente legale e commerciale.
Devi rispondere alla domanda dell'utente fondendo IN MODO LOGICO E CORRETTO le informazioni tratte dai documenti privati caricati dall'utente e le leggi italiane tratte dalla banca dati normativa.
REGOLA FONDAMENTALE 1: Cita chiaramente se un dato proviene dal "Documento Caricato" o dalla "Normativa".
REGOLA FONDAMENTALE 2: Non inventare mai leggi, articoli, scadenze, numeri finanziari o informazioni non presenti nei contesti.
REGOLA FONDAMENTALE 3: Se le informazioni non bastano a rispondere con certezza, dillo chiaramente.

=== CONTESTO DAI DOCUMENTI PRIVATI CARICATI ===
{context_docs}
================================================

=== CONTESTO NORMATIVO DALLA BANCA DATI ====
{context_laws}
================================================

DOMANDA DELL'UTENTE: {question}

RISPOSTA DETTAGLIATA (cita le fonti):"""

hybrid_prompt = PromptTemplate(template=hybrid_prompt_template, input_variables=["context_docs", "context_laws", "question"])

# =========================
# SIDEBAR
# =========================
st.sidebar.header("📁 Gestione Documenti")
app_mode = st.sidebar.radio("Scegli la base di conoscenza:", [
    "📚 Ricerca Normativa (Leggi)", 
    "📊 Analisi Documenti Privati",
    "🧠 Analisi Ibrida (Documenti + Leggi)"
])

if app_mode in ["📊 Analisi Documenti Privati", "🧠 Analisi Ibrida (Documenti + Leggi)"]:
    uploaded_files = st.sidebar.file_uploader(
        "Carica i tuoi documenti", 
        type=["pdf", "txt", "csv", "xlsx"], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        if st.sidebar.button("Elabora Documenti"):
            with st.spinner("Analisi e vettorializzazione dei documenti in corso..."):
                temp_db = process_uploaded_files(uploaded_files, embeddings)
                if temp_db:
                    st.session_state.temp_retriever = temp_db.as_retriever(search_kwargs={"k": 4})
                    st.sidebar.success("Documenti pronti per l'analisi!")
                else:
                    st.sidebar.error("Impossibile elaborare i documenti.")

    if st.sidebar.button("Pulisci Memoria Documenti"):
        if "temp_retriever" in st.session_state:
            del st.session_state["temp_retriever"]
        st.session_state.messages = []
        st.rerun()

# =========================
# MONITORAGGIO SISTEMA
# =========================
st.sidebar.markdown("---")
st.sidebar.header("📈 Stato Sistema")

@st.fragment(run_every="2s")
def render_system_monitor():
    cpu_usage = psutil.cpu_percent(interval=None)
    ram_usage = psutil.virtual_memory().percent

    gpu_mem = "N/D"
    if torch is not None:
        try:
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                allocated = torch.mps.current_allocated_memory() / (1024**2)
                gpu_mem = f"{allocated:.1f} MB"
            elif torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated() / (1024**2)
                gpu_mem = f"{allocated:.1f} MB"
        except Exception:
            pass

    gpu_util = "N/D"
    if sys.platform == "darwin":
        try:
            import subprocess, re
            res = subprocess.check_output(['ioreg', '-l'], text=True)
            match = re.search(r'"Device Utilization %"=([0-9]+)', res)
            if match:
                gpu_util = f"{match.group(1)}%"
        except Exception:
            pass

    col1, col2 = st.columns(2)
    col1.metric("CPU", f"{cpu_usage}%")
    col2.metric("RAM", f"{ram_usage}%")
    
    col3, col4 = st.columns(2)
    col3.metric("GPU Uso", gpu_util)
    col4.metric("GPU Mem", gpu_mem)

with st.sidebar:
    render_system_monitor()

# =========================
# CHAT INTERFACE
# =========================
# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add an initial greeting message from the assistant
    st.session_state.messages.append({"role": "assistant", "content": "Salve. Sono il tuo Assistente Commercialista locale. Come posso aiutarti oggi?"})

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If there are sources associated with the message, display them
        if "sources" in message and message["sources"]:
            with st.expander("📑 Fonti normative consultate"):
                for idx, source in enumerate(message["sources"]):
                    st.markdown(f"**[{idx+1}]** {source}")

# React to user input
if prompt := st.chat_input("Inserisci la tua ricerca legale..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Ricerca nel database e generazione risposta in corso..."):
            try:
                # Execution
                if app_mode == "📚 Ricerca Normativa (Leggi)":
                    result = qa_chain_laws.invoke({"query": prompt})
                    response = result['result']
                    
                    sources_list = []
                    for doc in result['source_documents']:
                        source_id = doc.metadata.get('source_id', 'Sconosciuta')
                        if source_id not in sources_list:
                            sources_list.append(source_id)
                            
                elif app_mode == "📊 Analisi Documenti Privati":
                    if "temp_retriever" not in st.session_state:
                        st.error("Devi prima caricare ed elaborare i documenti nella barra laterale.")
                        st.stop()
                        
                    qa_chain_docs = RetrievalQA.from_chain_type(
                        llm=llm,
                        chain_type="stuff",
                        retriever=st.session_state.temp_retriever,
                        return_source_documents=True,
                        chain_type_kwargs={"prompt": doc_prompt}
                    )
                    result = qa_chain_docs.invoke({"query": prompt})
                    response = result['result']
                    
                    sources_list = []
                    for doc in result['source_documents']:
                        source_id = doc.metadata.get('source_id', 'Sconosciuta')
                        if source_id not in sources_list:
                            sources_list.append(source_id)

                elif app_mode == "🧠 Analisi Ibrida (Documenti + Leggi)":
                    if "temp_retriever" not in st.session_state:
                        st.error("Devi prima caricare ed elaborare i documenti nella barra laterale.")
                        st.stop()
                    
                    # 1. Recupero frammenti documenti
                    docs_retrieved = st.session_state.temp_retriever.invoke(prompt)
                    context_docs = "\n\n".join([d.page_content for d in docs_retrieved])
                    
                    # 2. Recupero frammenti leggi
                    laws_retrieved = laws_retriever.invoke(prompt)
                    context_laws = "\n\n".join([d.page_content for d in laws_retrieved])
                    
                    # 3. Costruzione e Chiamata LLM Custom
                    formatted_prompt = hybrid_prompt.format(
                        context_docs=context_docs, 
                        context_laws=context_laws, 
                        question=prompt
                    )
                    response = llm.invoke(formatted_prompt)
                    
                    # 4. Unione fonti visive
                    sources_list = []
                    for doc in docs_retrieved:
                        src = f"[DOC] {doc.metadata.get('source_id', 'Documento Personale')}"
                        if src not in sources_list: sources_list.append(src)
                    for doc in laws_retrieved:
                        src = f"[LEGGE] {doc.metadata.get('source_id', 'Normativa Ufficiale')}"
                        if src not in sources_list: sources_list.append(src)
                
                # Display the response
                st.markdown(response)
                
                # Display the sources
                if sources_list:
                    with st.expander("📑 Fonti normative consultate"):
                        for i, source in enumerate(sources_list):
                            st.markdown(f"**[{i+1}]** {source}")
                            
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response,
                    "sources": sources_list
                })
            except Exception as e:
                error_msg = f"❌ Errore critico: `{e}`. Assicurati che Ollama sia in esecuzione e che il modello `{LLM_MODEL_NAME}` sia installato."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
