import os
import time
import logging
import signal
import sys
from dotenv import load_dotenv
from romm_client import RomMClient
from watcher import SaveWatcher
from sync_manager import SyncManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('steam_rom_sync.log')
    ]
)

def main():
    if not os.path.exists(".env"):
        logging.info("No .env found. Attempting to launch setup UI...")
        try:
            # Try to import customtkinter to see if we can run the UI
            import customtkinter
            from setup_ui import SetupWizard
            app = SetupWizard()
            app.mainloop()
        except ImportError:
            logging.error("setup_ui.py requires 'customtkinter'. Please run 'pip install customtkinter' or use install.sh")
            return
        except Exception as e:
            logging.error(f"Failed to launch setup UI: {e}")
            return

    load_dotenv()

    romm_url = os.getenv("ROMM_URL")
    romm_api_key = os.getenv("ROMM_API_KEY")
    romm_username = os.getenv("ROMM_USERNAME")
    romm_password = os.getenv("ROMM_PASSWORD")
    monitor_paths_raw = os.getenv("MONITOR_PATHS", "")
    
    if not romm_url:
        logging.error("ROMM_URL not set in .env")
        return

    if not (romm_api_key or (romm_username and romm_password)):
        logging.warning("Authentication not configured. If your RomM instance requires it, syncing will fail.")

    monitor_paths = [p.strip() for p in monitor_paths_raw.split(",") if p.strip()]
    
    # Filter out non-existent paths
    valid_paths = []
    for p in monitor_paths:
        if os.path.exists(p):
            valid_paths.append(p)
        else:
            logging.warning(f"Configured path does not exist: {p}")

    if not valid_paths:
        logging.error("No valid monitoring paths found. Exiting.")
        return

    client = RomMClient(romm_url, api_key=romm_api_key, username=romm_username, password=romm_password)
    
    if not client.check_heartbeat():
        logging.error("Could not reach RomM instance. Please check your ROMM_URL and network connection.")
    else:
        logging.info("Successfully connected to RomM heartbeat.")
    sync_manager = SyncManager(client)
    watcher = SaveWatcher(valid_paths, sync_manager.handle_save_change)

    logging.info("Starting SteamRomSync...")
    watcher.start()

    def signal_handler(sig, frame):
        logging.info("Stopping SteamRomSync...")
        watcher.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()

if __name__ == "__main__":
    main()
