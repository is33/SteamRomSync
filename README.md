# SteamRomSync

A background service for Steam Deck / SteamOS that automatically synchronizes emulator save files to your [RomM](https://github.com/romm-manager/romm) instance.

## Features
- **Automatic Monitoring:** Uses filesystem watchers to detect save file changes in real-time.
- **RetroArch Support:** Automatically maps `.srm` and `.sav` files to RomM entries.
- **Vita3K Support:** Detects Vita3K Title ID structures and maps them to RomM.
- **Background Service:** Runs as a systemd user service on SteamOS.
- **Save Manager UI:** A desktop application to browse and restore previous save versions from RomM.
- **Debounced Uploads:** Prevents multiple uploads during rapid save operations.

## Installation & Setup

1. **Clone or Download** this repository to your Steam Deck.
2. **Open Konsole** and navigate to the folder:
   ```bash
   cd ~/Downloads/SteamRomSync
   ```
3. **Launch the Setup UI**:
   ```bash
   # The installer will set up dependencies and open the Setup Wizard
   chmod +x install.sh
   ./install.sh
   ```
4. **Follow the Wizard**: The Steam Deck-styled UI will walk you through connecting your RomM instance and selecting your save paths.

5. **Finished!** The wizard will automatically install and start the background service for you.

## Manual Configuration (Optional)
If you prefer to configure manually or are on a headless system:
1. Copy `.env.example` to `.env`.
2. Edit the `.env` file with your `ROMM_URL`, `ROMM_API_KEY` (or credentials), and `MONITOR_PATHS`.
3. Restart the service: `systemctl --user restart steamromsync.service`

## Logs
You can monitor the sync activity using:
```bash
journalctl --user -u steamromsync.service -f
```
Or check the local log file:
```bash
tail -f steam_rom_sync.log
```
