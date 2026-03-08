#!/bin/bash
# ==========================================
# STEP 5: GRAPHICAL INFERENCE ENVIRONMENT SETUP
# ==========================================

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd "$SCRIPT_DIR" || exit

echo "1. Creating the virtual environment (venv) for Step 5..."
python3 -m venv venv

echo "2. Activating the virtual environment..."
source venv/bin/activate

echo "3. Installing AI libraries (LangChain, ChromaDB, Sentence-Transformers, Streamlit)..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "Environment ready! To start the chatbot, run:"
echo "source venv/bin/activate"
echo "streamlit run app.py"
echo "=========================================="
