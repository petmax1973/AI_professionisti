#!/bin/bash
# Script to quickly create the virtual environment and install dependencies for Step 6 (macOS Apple Silicon)

echo "1. Creating the virtual environment (venv)..."
python3 -m venv venv

echo "2. Activating the virtual environment..."
source venv/bin/activate

echo "3. Installing AI libraries for Apple Silicon (MLX)..."
pip install --upgrade pip
pip install mlx-lm datasets

echo "Environment ready! To start fine-tuning, run:"
echo "source venv/bin/activate"
