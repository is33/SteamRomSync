# SteamRomSync

A background service for Steam Deck / SteamOS that automatically synchronizes emulator save files to your [RomM](https://github.com/romm-manager/romm) instance.

## Features
- **Automatic Monitoring:** Uses filesystem watchers to detect save file changes in real-time.
- **RetroArch Support:** Automatically maps `.srm` and `.sav` files to RomM entries.
- **Vita3K Support:** Detects Vita3K Title ID structures and maps them to RomM.
- **Background Service:** Runs as a systemd user service on SteamOS.
- **Debounced Uploads:** Prevents multiple uploads during rapid save operations.

## Installation

1. **Clone or Download** this repository to your Steam Deck.
2. **Open Konsole** and navigate to the folder:
   ```bash
   cd ~/Downloads/SteamRomSync
   ```
3. **Run the installer**:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

## Configuration

1. Edit the `.env` file in the project directory:
   ```bash
   nano .env
   ```
2. Fill in your RomM details:
   - `ROMM_URL`: The full URL to your RomM instance (e.g., `http://192.168.1.10:3000`).
   - `ROMM_API_KEY`: Your RomM API key or Bearer token.
   - `MONITOR_PATHS`: Comma-separated list of directories to watch. (Default EmuDeck paths are provided in `.env.example`).

3. **Restart the service** to apply changes:
   ```bash
   systemctl --user restart steamromsync.service
   ```

## Logs
You can monitor the sync activity using:
```bash
journalctl --user -u steamromsync.service -f
```
Or check the local log file:
```bash
tail -f steam_rom_sync.log
```
