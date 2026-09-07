#!/bin/bash

# Set working directory to the project root
cd "$(dirname "$0")/.."

echo "=========================================================="
echo "Starting Smart Building Management System (Linux)..."
echo "=========================================================="

# Check if virtual environment exists
if [ ! -f "venv/bin/python" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run 'bash linux/install.sh' first to setup the system."
    exit 1
fi

# Get the local IP address safely
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')

echo ""
echo "=========================================================="
echo "Server is starting..."
echo "You can view the app from THIS computer at:"
echo "http://localhost:8000"
echo ""
echo "To access the app from ANY DEVICE on your Wi-Fi/Network:"
if [ ! -z "$LOCAL_IP" ]; then
    echo "http://$LOCAL_IP:8000"
else
    echo "[Could not detect local IP automatically]"
fi
echo "=========================================================="
echo ""
echo "NOTE: Ensure your Linux firewall (ufw or iptables) allows traffic on port 8000."
echo "e.g. 'sudo ufw allow 8000'"
echo ""

./venv/bin/uvicorn maintestfinal2:app --host 0.0.0.0 --port 8000 --reload
