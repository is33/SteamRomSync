import os
import logging
from romm_client import RomMClient
from notifications import NotificationManager

class SyncManager:
    def __init__(self, client: RomMClient, monitor_paths=None, exclusion_list=None, save_keep_count=0):
        self.client = client
        self.rom_id_cache = {}
        self.monitor_paths = monitor_paths or []
        self.exclusion_list = exclusion_list or []
        self.save_keep_count = save_keep_count
        self.last_sync_times = {} # path -> mtime

    def perform_full_scan(self):
        """Discovers and syncs all changed save files."""
        from discovery import discover_save_files
        logging.info("Starting full save discovery scan...")
        files = discover_save_files(self.monitor_paths)
        
        for file_path in files:
            try:
                # Check exclusion list
                if self.is_excluded(file_path):
                    logging.debug(f"Skipping excluded path: {file_path}")
                    continue

                mtime = os.path.getmtime(file_path)
                if file_path in self.last_sync_times:
                    if mtime <= self.last_sync_times[file_path]:
                        continue # Already synced this version
                
                self.handle_save_change(file_path)
                self.last_sync_times[file_path] = mtime
            except Exception as e:
                logging.error(f"Error during scan for {file_path}: {e}")
        
        logging.info("Full scan complete.")

    def is_excluded(self, file_path):
        """Checks if a file or its directory is in the exclusion list."""
        filename = os.path.basename(file_path)
        for exclusion in self.exclusion_list:
            if exclusion.lower() in file_path.lower() or exclusion.lower() in filename.lower():
                return True
        return False

    def handle_save_change(self, file_path):
        """Processes a save file change."""
        if self.is_excluded(file_path):
            return

        filename = os.path.basename(file_path)
        
        # Filter by common save extensions
        save_extensions = {
            '.srm', '.sav', '.state', '.bsv', '.nvram', '.ups', '.ips', # General/RetroArch
            '.ps2', # PCSX2
            '.gci', '.raw', # Dolphin/GameCube
            '.vmp', '.mcd' # PS1/PS2 MemCards
        }
        ext = os.path.splitext(filename)[1].lower()
        
        is_vita = "savedata" in file_path and "Vita3K" in file_path
        
        if not is_vita and ext not in save_extensions:
            return

        # Detect ROM name from structure
        rom_name = self.detect_rom_name(file_path, filename, is_vita)
        
        logging.info(f"Syncing save for: {rom_name}")
        
        rom_id = self.get_rom_id(rom_name)
        
        if rom_id:
            try:
                self.client.upload_save(rom_id, file_path)
                logging.info(f"Successfully uploaded save for {rom_name} (ID: {rom_id})")
                
                # Cleanup old versions if configured
                if self.save_keep_count > 0:
                    self.perform_cleanup(rom_id)
                
                # Notify success
                NotificationManager.notify_success(rom_name, filename)
            except Exception as e:
                logging.error(f"Failed to upload save for {rom_name}: {e}")
                NotificationManager.notify_error(f"Failed to sync {rom_name}: {e}")
        else:
            logging.warning(f"Could not find ROM ID for {rom_name}. Skipping.")

    def detect_rom_name(self, file_path, filename, is_vita):
        """Improved ROM name detection for various emulators."""
        if is_vita:
            parts = file_path.split(os.sep)
            try:
                idx = parts.index("savedata")
                return parts[idx + 1]
            except (ValueError, IndexError):
                pass
        
        # PCSX2 often uses Serial as filename (e.g. SLUS-20071.ps2)
        # Dolphin might use GameID (e.g. GZLE01.sav)
        # For now, we strip extension. Future: Serial to Name lookup if needed.
        return os.path.splitext(filename)[0]

    def perform_cleanup(self, rom_id):
        """Deletes oldest save versions if they exceed save_keep_count."""
        try:
            saves = self.client.get_saves_for_rom(rom_id)
            if len(saves) > self.save_keep_count:
                # Sort by added_at (assuming ISO format or similar that sorts well)
                saves.sort(key=lambda x: x.get("added_at", ""), reverse=True)
                
                # Keep the newest N, delete the rest
                to_delete = saves[self.save_keep_count:]
                for save in to_delete:
                    save_id = save.get("id")
                    if save_id:
                        self.client.delete_save(save_id)
                
                logging.info(f"Cleaned up {len(to_delete)} old save versions for ROM ID {rom_id}")
        except Exception as e:
            logging.error(f"Save cleanup failed for ROM ID {rom_id}: {e}")

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
