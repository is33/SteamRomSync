#!/bin/bash

# SteamRomSync Uninstaller for Steam Deck

SERVICE_NAME="steamromsync.service"
USER_SYSTEMD_DIR="$HOME/.config/systemd/user"
DESKTOP_FILE="$HOME/Desktop/SteamRomSync-Manager.desktop"

echo "Uninstalling SteamRomSync..."

# Stop and disable service
if systemctl --user is-active --quiet "$SERVICE_NAME"; then
    echo "Stopping service..."
    systemctl --user stop "$SERVICE_NAME"
fi

if systemctl --user is-enabled --quiet "$SERVICE_NAME"; then
    echo "Disabling service..."
    systemctl --user disable "$SERVICE_NAME"
fi

# Remove service file
if [ -f "$USER_SYSTEMD_DIR/$SERVICE_NAME" ]; then
    echo "Removing service file..."
    rm "$USER_SYSTEMD_DIR/$SERVICE_NAME"
    systemctl --user daemon-reload
fi

# Remove desktop shortcut
if [ -f "$DESKTOP_FILE" ]; then
    echo "Removing desktop shortcut..."
    rm "$DESKTOP_FILE"
fi

echo "SteamRomSync system components have been removed."
echo "Note: The project folder, virtual environment, and .env configuration were NOT deleted."
