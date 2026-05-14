#!/bin/bash

# SteamRomSync Updater for Steam Deck
# This script handles both existing git repos and "un-gitted" ZIP installs.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SERVICE_NAME="steamromsync.service"
REPO_URL="https://github.com/is33/SteamRomSync.git"
BRANCH="beta"

echo "Checking for SteamRomSync updates..."

cd "$SCRIPT_DIR"

# Self-Healing: Check if this is a git repository
if [ ! -d ".git" ]; then
    echo "This folder is not a git repository. Initializing connection to GitHub..."
    git init
    git remote add origin "$REPO_URL"
fi

# Ensure remote URL is correct
git remote set-url origin "$REPO_URL"

echo "Pulling latest changes from $BRANCH branch..."
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

# Ensure scripts remain executable
chmod +x "$SCRIPT_DIR/install.sh"
chmod +x "$SCRIPT_DIR/uninstall.sh"
chmod +x "$SCRIPT_DIR/update.sh"

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

echo "Update complete! All files have been synchronized."
