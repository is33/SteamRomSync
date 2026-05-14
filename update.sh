#!/bin/bash

# SteamRomSync Updater for Steam Deck

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SERVICE_NAME="steamromsync.service"

echo "Updating SteamRomSync..."

cd "$SCRIPT_DIR"

# Pull latest changes
if [ -d ".git" ]; then
    echo "Pulling latest changes from git..."
    git pull
else
    echo "Git repository not found, skipping git pull."
fi

# Update dependencies
if [ -d "venv" ]; then
    echo "Updating dependencies in virtual environment..."
    "./venv/bin/pip" install -r "requirements.txt"
else
    echo "Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Restart service
echo "Restarting service..."
systemctl --user daemon-reload
systemctl --user restart "$SERVICE_NAME"

echo "Update complete!"
