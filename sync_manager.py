import os
import logging
from romm_client import RomMClient

class SyncManager:
    def __init__(self, client: RomMClient, monitor_paths=None):
        self.client = client
        self.rom_id_cache = {}
        self.monitor_paths = monitor_paths or []
        self.last_sync_times = {} # path -> mtime

    def perform_full_scan(self):
        """Discovers and syncs all changed save files."""
        from discovery import discover_save_files
        logging.info("Starting full save discovery scan...")
        files = discover_save_files(self.monitor_paths)
        
        for file_path in files:
            try:
                mtime = os.path.getmtime(file_path)
                if file_path in self.last_sync_times:
                    if mtime <= self.last_sync_times[file_path]:
                        continue # Already synced this version
                
                self.handle_save_change(file_path)
                self.last_sync_times[file_path] = mtime
            except Exception as e:
                logging.error(f"Error during scan for {file_path}: {e}")
        
        logging.info("Full scan complete.")

    def handle_save_change(self, file_path):
        """Processes a save file change."""
        filename = os.path.basename(file_path)
        
        # Filter by common save extensions
        save_extensions = {'.srm', '.sav', '.state', '.bsv', '.nvram', '.ups', '.ips'}
        ext = os.path.splitext(filename)[1].lower()
        
        # Vita3K often uses specific file structures, we might want to be more inclusive there
        # but for RetroArch and general, we stick to save extensions
        is_vita = "savedata" in file_path and "Vita3K" in file_path
        
        if not is_vita and ext not in save_extensions:
            return

        # Detect Vita3K structure: .../savedata/<TitleID>/...
        if is_vita:
            parts = file_path.split(os.sep)
            try:
                # Find the index of 'savedata' and get the next part
                idx = parts.index("savedata")
                rom_name = parts[idx + 1]
            except (ValueError, IndexError):
                rom_name = os.path.splitext(filename)[0]
        else:
            rom_name = os.path.splitext(filename)[0]
        
        logging.info(f"Syncing save for: {rom_name}")
        
        rom_id = self.get_rom_id(rom_name)
        
        if rom_id:
            try:
                self.client.upload_save(rom_id, file_path)
                logging.info(f"Successfully uploaded save for {rom_name} (ID: {rom_id})")
            except Exception as e:
                logging.error(f"Failed to upload save for {rom_name}: {e}")
        else:
            logging.warning(f"Could not find ROM ID for {rom_name}. Skipping.")

    def get_rom_id(self, rom_name):
        """Gets the RomM ID for a ROM name, using cache if available."""
        if rom_name in self.rom_id_cache:
            return self.rom_id_cache[rom_name]
        
        try:
            rom_id = self.client.search_rom(rom_name)
            if rom_id:
                self.rom_id_cache[rom_name] = rom_id
                return rom_id
        except Exception as e:
            logging.error(f"Error searching for ROM {rom_name}: {e}")
            
        return None
