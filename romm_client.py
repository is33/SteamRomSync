import requests
import os
import logging
from requests.auth import HTTPBasicAuth
from thefuzz import process

class RomMClient:
    def __init__(self, base_url, api_key=None, username=None, password=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        if username and password:
            self.session.auth = HTTPBasicAuth(username, password)
            logging.info("RomMClient: Using Basic Authentication")
        elif api_key:
            # Although you mentioned BasicAuth, keeping Bearer as a fallback if no username/pass
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
            logging.info("RomMClient: Using Bearer Token Authentication")
        else:
            logging.warning("RomMClient: No authentication provided. Some endpoints may fail.")

    def check_heartbeat(self):
        """Checks if the RomM instance is reachable and authenticated."""
        url = f"{self.base_url}/api/heartbeat"
        try:
            # Use session to ensure auth is applied
            response = self.session.get(url, timeout=5)
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
        """Uploads a save file to RomM with a timestamped filename for versioning."""
        url = f"{self.base_url}/api/saves"
        
        # Use query parameters as defined in API docs
        params = {
            'rom_id': int(rom_id),
            'overwrite': 'true'
        }
        if emulator:
            params['emulator'] = emulator

        # Standard multipart upload
        filename = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            # Many RomM versions expect 'file' as the key.
            # Using tuple format to ensure filename and content-type are sent.
            files = {
                'file': (filename, f, 'application/octet-stream')
            }

            logging.info(f"Uploading {filename} to RomM (ID: {rom_id})...")
            
            # Using session to ensure headers/auth are preserved
            response = self.session.post(url, params=params, files=files, timeout=60)
            
            if response.status_code != 200:
                logging.error(f"Upload failed: {response.status_code} - {response.text}")
            
            response.raise_for_status()
            return response.json()

    def delete_save(self, save_id):
        """Deletes a specific save file from RomM."""
        url = f"{self.base_url}/api/saves/{save_id}"
        try:
            logging.info(f"Deleting save ID: {save_id} from RomM...")
            response = self.session.delete(url)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"Failed to delete save {save_id}: {e}")
            return False

    def get_all_saves(self):
        """Fetches all save records from RomM."""
        url = f"{self.base_url}/api/saves"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Failed to fetch saves: {e}")
            return []

    def get_saves_for_rom(self, rom_id):
        """Fetches all saves for a specific ROM ID."""
        url = f"{self.base_url}/api/saves"
        params = {"rom_id": rom_id}
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Failed to fetch saves for ROM {rom_id}: {e}")
            return []

    def download_save(self, save_id, target_path):
        """Downloads a specific save file to the target path."""
        url = f"{self.base_url}/api/saves/{save_id}"
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            logging.error(f"Failed to download save {save_id}: {e}")
            return False

    def search_rom(self, search_term):
        """Searches for a ROM ID based on a search term using fuzzy matching.
        Returns: (rom_id, matched_name, score) or None
        """
        url = f"{self.base_url}/api/roms"
        params = {
            "search_term": search_term, # Correct parameter name for this RomM version
            "page": 1,
            "page_size": 50
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # This version of RomM uses 'items' key for results
            if isinstance(data, dict):
                results = data.get("items", data.get("roms", data.get("results", [])))
                if not results and not any(k in data for k in ["items", "roms", "results"]):
                    # If it's a dict but no known keys, it might be a single object or empty list
                    results = [data] if data.get("id") else []
            elif isinstance(data, list):
                results = data
            else:
                results = []
            
            if not results:
                logging.warning(f"No results found for {search_term}")
                return None

            rom_map = {}
            for rom in results:
                if not isinstance(rom, dict):
                    continue
                    
                # Use name or filename/path for matching
                display_name = rom.get("name") or rom.get("fs_name") or os.path.basename(rom.get("fs_path", ""))
                if display_name:
                    rom_map[display_name] = rom

            if not rom_map:
                if results and isinstance(results[0], dict):
                    res = results[0]
                    return res.get("id"), res.get("name"), 0
                return None

            # Perform fuzzy matching
            match, score = process.extractOne(search_term, rom_map.keys())
            
            logging.info(f"Fuzzy search for '{search_term}': Best match '{match}' with score {score}")
            
            if score >= 70:
                rom_obj = rom_map[match]
                return rom_obj.get("id"), match, score
            
            # Fallback to first valid result
            for res in results:
                if isinstance(res, dict) and res.get("id"):
                    return res.get("id"), res.get("name"), 0
            
            return None
            
        except Exception as e:
            logging.error(f"Search failed for {search_term}: {e}")
            return None

