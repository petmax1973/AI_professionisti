#!/bin/bash
# ==========================================
# STEP 1: DOWNLOAD LAWS ENVIRONMENT SETUP
# ==========================================

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd "$SCRIPT_DIR" || exit

echo "1. Creating the virtual environment (venv) for Step 1..."
python3 -m venv venv

echo "2. Activating the virtual environment..."
source venv/bin/activate

echo "3. Installing required libraries (requests)..."
pip install --upgrade pip
pip install requests==2.32.5

echo ""
echo "=========================================="
echo "Environment ready! To start downloading laws, run:"
echo "source venv/bin/activate"
echo "python export_laws_2.py"
echo "=========================================="
