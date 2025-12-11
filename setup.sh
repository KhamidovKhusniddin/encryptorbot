#!/bin/bash
echo "Installing Python dependencies (Telebot version)..."

# Install system dependencies
if ! dpkg -s python3-pip python3-venv &> /dev/null; then
    echo "Installing system packages..."
    apt-get update
    apt-get install -y python3-pip python3-venv
fi

# Clean old venv if broken
if [ -d "venv" ]; then
    if [ ! -f "venv/bin/activate" ]; then
        echo "Removing broken venv..."
        rm -rf venv
    fi
fi

# Create venv
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Fix permissions if needed
chmod -R 755 venv

# Activate and Install
source venv/bin/activate
echo "Installing libraries into venv..."
pip install --upgrade pip
pip install -r requirements.txt

# Run
echo "Starting Bot..."
python3 main.py
