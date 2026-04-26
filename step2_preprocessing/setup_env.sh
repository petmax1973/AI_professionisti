#!/bin/bash
# Script to quickly create the virtual environment and install dependencies for Step 2

echo "1. Creating the virtual environment (venv)..."
python3 -m venv venv

echo "2. Activating the virtual environment..."
source venv/bin/activate

echo "3. Installing libraries (PyMuPDF, langchain-text-splitters)..."
pip install --upgrade pip
pip install PyMuPDF langchain-text-splitters

echo "Environment ready! To start the process, run:"
echo "source venv/bin/activate"
echo "python3 preprocess_agenzia.py"
