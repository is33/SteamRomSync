import requests
import os
import logging
from requests.auth import HTTPBasicAuth

class RomMClient:
    def __init__(self, base_url, api_key=None, username=None, password=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        if username and password:
            self.session.auth = HTTPBasicAuth(username, password)
            logging.info("RomMClient: Using Basic Authentication")
        elif api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
            logging.info("RomMClient: Using Bearer Token Authentication")
        else:
            logging.warning("RomMClient: No authentication provided. Some endpoints may fail.")

    def check_heartbeat(self):
        """Checks if the RomM instance is reachable."""
        url = f"{self.base_url}/api/heartbeat"
        try:
            response = requests.get(url, timeout=5) # Use direct requests to avoid session auth for heartbeat
            if response.status_code == 200:
                logging.info("RomM Heartbeat: OK")
                return True
            else:
                logging.error(f"RomM Heartbeat: Failed with status {response.status_code}")
                return False
        except Exception as e:
            logging.error(f"RomM Heartbeat: Error connecting to {url}: {e}")
            return False

    def upload_save(self, rom_id, file_path, emulator=None):
        """Uploads a save file to RomM."""
        url = f"{self.base_url}/api/saves"
        
        filename = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            files = {
                'file': (filename, f, 'application/octet-stream')
            }
            data = {
                'rom_id': rom_id,
            }
            if emulator:
                data['emulator'] = emulator

            logging.info(f"Uploading {filename} to RomM (ID: {rom_id})...")
            response = self.session.post(url, files=files, data=data)
            
            if response.status_code != 200:
                logging.error(f"Upload failed: {response.status_code} - {response.text}")
            
            response.raise_for_status()
            return response.json()

    def search_rom(self, search_term):
        """Searches for a ROM ID based on a search term (filename or title)."""
        url = f"{self.base_url}/api/roms"
        params = {
            "search": search_term,
            "page": 1,
            "page_size": 10
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # The structure is usually {"roms": [...], "total": ...} or just a list
            results = data.get("roms", data) if isinstance(data, dict) else data
            
            if not results:
                return None

            # Look for an exact match in 'name' or 'path'
            for rom in results:
                # 'path' usually contains the filename on disk
                rom_path = rom.get("path", "")
                rom_name = rom.get("name", "")
                
                if search_term.lower() in rom_path.lower() or search_term.lower() == rom_name.lower():
                    return rom.get("id")
            
            # Fallback to first result if no exact match but we found something
            return results[0].get("id")
            
        except Exception as e:
            logging.error(f"Search failed for {search_term}: {e}")
            return None
