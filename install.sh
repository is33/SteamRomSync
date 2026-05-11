#!/bin/bash

# SteamRomSync Installer for Steam Deck

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SERVICE_NAME="steamromsync.service"
USER_SYSTEMD_DIR="$HOME/.config/systemd/user"

echo "Setting up SteamRomSync in $SCRIPT_DIR..."

# Create virtual environment if it doesn't exist
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
fi

# Install dependencies
echo "Installing dependencies..."
"$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

# Update service file with correct path
echo "Configuring systemd service..."
sed -i "s|ExecStart=.*|ExecStart=$SCRIPT_DIR/venv/bin/python3 $SCRIPT_DIR/main.py|" "$SCRIPT_DIR/$SERVICE_NAME"
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$SCRIPT_DIR|" "$SCRIPT_DIR/$SERVICE_NAME"

# Create systemd directory if it doesn't exist
mkdir -p "$USER_SYSTEMD_DIR"

# Link or copy service file
cp "$SCRIPT_DIR/$SERVICE_NAME" "$USER_SYSTEMD_DIR/"

# Reload systemd and enable service
echo "Enabling and starting service..."
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user start "$SERVICE_NAME"

# Ensure service runs even when not in Desktop mode
echo "Enabling linger for 'deck' user to ensure persistence..."
loginctl enable-linger deck

echo "Installation complete!"

if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "No configuration found. Launching Setup Wizard..."
    "$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/main.py"
else
    echo "Configuration found. Restarting service..."
    systemctl --user restart "$SERVICE_NAME"
fi

echo "All set! You can check the logs with: journalctl --user -u $SERVICE_NAME -f"
