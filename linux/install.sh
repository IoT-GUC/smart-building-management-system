#!/bin/bash
# Smart Building Management System - Linux Installation Script
# Run this script as a normal user (it will ask for sudo password when needed)

set -e

# Set working directory to the project root
cd "$(dirname "$0")/.."

echo "=========================================================="
echo "Installing Smart Building Management System (Linux)"
echo "=========================================================="

# 1. System Requirements
echo "[1/4] Installing system dependencies (requires sudo)..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv sqlite3

# 2. Virtual Environment
echo "[2/4] Setting up Python virtual environment..."
python3 -m venv venv

# 3. Python Dependencies
echo "[3/4] Installing Python requirements..."
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt

# 4. Directories setup
echo "[4/4] Creating necessary directories..."
mkdir -p uploads

echo "=========================================================="
echo "Installation Complete!"
echo "=========================================================="
echo "To start the application, run the following command:"
echo "  ./linux/run.sh"
echo "=========================================================="
