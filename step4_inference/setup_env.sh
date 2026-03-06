#!/bin/bash
# ==========================================
# STEP 4: INFERENCE ENVIRONMENT SETUP
# ==========================================

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd "$SCRIPT_DIR" || exit

echo "1. Creating the virtual environment (venv) for Step 4..."
python3 -m venv venv

echo "2. Activating the virtual environment..."
source venv/bin/activate

echo "3. Installing AI libraries (LangChain, ChromaDB, Sentence-Transformers)..."
pip install --upgrade pip
pip install langchain==0.2.14 langchain-community==0.2.12 langchain-huggingface==0.0.3 chromadb==0.5.5 sentence-transformers==3.0.1 pydantic==2.8.2

echo ""
echo "=========================================="
echo "Environment ready! To start the chatbot, run:"
echo "source venv/bin/activate"
echo "python3 chat_rag.py"
echo "=========================================="
