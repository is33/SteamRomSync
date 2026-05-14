#!/bin/bash

# SteamRomSync Updater for Steam Deck
# This script handles code updates, systemd services, and desktop shortcuts.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SERVICE_NAME="steamromsync.service"
USER_SYSTEMD_DIR="$HOME/.config/systemd/user"
DESKTOP_FILE="$HOME/Desktop/SteamRomSync-Manager.desktop"
REPO_URL="https://github.com/is33/SteamRomSync.git"
BRANCH="beta"

echo "Checking for SteamRomSync updates..."

cd "$SCRIPT_DIR"

# 1. Self-Healing: Check if this is a git repository
if [ ! -d ".git" ]; then
    echo "This folder is not a git repository. Initializing connection to GitHub..."
    git init
    git remote add origin "$REPO_URL"
fi

# Ensure remote URL is correct
git remote set-url origin "$REPO_URL"

echo "Synchronizing with $BRANCH branch..."
git fetch origin "$BRANCH"

# 2. Force switch to the correct branch and align with remote
git checkout -f -B "$BRANCH" "origin/$BRANCH"
git reset --hard "origin/$BRANCH"
git branch --set-upstream-to="origin/$BRANCH" "$BRANCH"

# Ensure scripts remain executable
chmod +x "$SCRIPT_DIR/install.sh"
chmod +x "$SCRIPT_DIR/uninstall.sh"
chmod +x "$SCRIPT_DIR/update.sh"

# 3. Update dependencies
if [ -d "venv" ]; then
    echo "Updating dependencies in virtual environment..."
    "./venv/bin/pip" install -r "requirements.txt"
else
    echo "Virtual environment not found. Please run install.sh first."
    exit 1
fi

# 4. Refresh Systemd Service (in case ExecStart or paths changed)
echo "Refreshing systemd service configuration..."
sed -i "s|ExecStart=.*|ExecStart=$SCRIPT_DIR/venv/bin/python3 $SCRIPT_DIR/main.py|" "$SCRIPT_DIR/$SERVICE_NAME"
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$SCRIPT_DIR|" "$SCRIPT_DIR/$SERVICE_NAME"
mkdir -p "$USER_SYSTEMD_DIR"
cp "$SCRIPT_DIR/$SERVICE_NAME" "$USER_SYSTEMD_DIR/"

# 5. Refresh Desktop Shortcut (in case icon or paths changed)
echo "Refreshing desktop shortcut..."
cat > "$DESKTOP_FILE" <<EOL
[Desktop Entry]
Name=SteamRomSync Manager
Comment=Manage and restore emulator saves from RomM
Exec=$SCRIPT_DIR/venv/bin/python3 $SCRIPT_DIR/manager_ui.py
Icon=system-software-update
Terminal=false
Type=Application
Categories=Game;Utility;
Path=$SCRIPT_DIR
EOL
chmod +x "$DESKTOP_FILE"

# 6. Restart service to apply all changes
echo "Restarting service..."
systemctl --user daemon-reload
systemctl --user restart "$SERVICE_NAME"

echo "Update complete! The background service and Save Manager application have been refreshed."
