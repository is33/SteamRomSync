import customtkinter as ctk
import os
import logging
import re
from pathlib import Path
from dotenv import load_dotenv
from romm_client import RomMClient

# Configure logging
logging.basicConfig(level=logging.INFO)

class SaveManager(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SteamRomSync Save Manager")
        self.geometry("800x600")
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        load_dotenv()
        self.romm_url = os.getenv("ROMM_URL")
        self.romm_api_key = os.getenv("ROMM_API_KEY")
        self.romm_username = os.getenv("ROMM_USERNAME")
        self.romm_password = os.getenv("ROMM_PASSWORD")
        self.monitor_paths = [p.strip() for p in os.getenv("MONITOR_PATHS", "").split(",") if p.strip()]

        if not self.romm_url:
            self.show_error("ROMM_URL not found. Please run setup.")
            return

        self.client = RomMClient(self.romm_url, api_key=self.romm_api_key, username=self.romm_username, password=self.romm_password)
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # Left Sidebar: Navigation
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.sidebar_label = ctk.CTkLabel(self.sidebar, text="SRS Manager", font=("Helvetica", 20, "bold"))
        self.sidebar_label.pack(pady=20)
        
        self.btn_roms = ctk.CTkButton(self.sidebar, text="Saves", command=self.show_rom_view)
        self.btn_roms.pack(fill="x", pady=10, padx=10)
        
        self.btn_settings = ctk.CTkButton(self.sidebar, text="Settings", command=self.show_settings_view)
        self.btn_settings.pack(fill="x", pady=10, padx=10)

        # Right Main: Content Area
        self.main_view = ctk.CTkFrame(self)
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.show_rom_view()

    def show_rom_view(self):
        # Clear main view
        for widget in self.main_view.winfo_children():
            widget.destroy()

        self.rom_title = ctk.CTkLabel(self.main_view, text="Select a game from the list", font=("Helvetica", 24, "bold"))
        self.rom_title.pack(pady=20)
        
        container = ctk.CTkFrame(self.main_view)
        container.pack(fill="both", expand=True)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=2)
        container.grid_rowconfigure(0, weight=1)

        self.rom_listbox = ctk.CTkScrollableFrame(container, label_text="ROMs")
        self.rom_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.version_list = ctk.CTkScrollableFrame(container, label_text="Save Versions")
        self.version_list.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.load_data()

    def show_settings_view(self):
        # Clear main view
        for widget in self.main_view.winfo_children():
            widget.destroy()

        self.rom_title = ctk.CTkLabel(self.main_view, text="Settings", font=("Helvetica", 24, "bold"))
        self.rom_title.pack(pady=20)

        settings_frame = ctk.CTkScrollableFrame(self.main_view)
        settings_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Exclusion List
        ctk.CTkLabel(settings_frame, text="Exclusion List (Comma separated names/paths)", font=("Helvetica", 14, "bold")).pack(pady=(10, 5), padx=10, anchor="w")
        self.exclusion_entry = ctk.CTkEntry(settings_frame, width=500)
        self.exclusion_entry.insert(0, os.getenv("EXCLUSION_LIST", ""))
        self.exclusion_entry.pack(pady=5, padx=10, fill="x")

        # Save Keep Count
        ctk.CTkLabel(settings_frame, text="Save Versions to Keep (0 = Unlimited)", font=("Helvetica", 14, "bold")).pack(pady=(20, 5), padx=10, anchor="w")
        self.keep_count_entry = ctk.CTkEntry(settings_frame, width=100)
        self.keep_count_entry.insert(0, os.getenv("SAVE_KEEP_COUNT", "0"))
        self.keep_count_entry.pack(pady=5, padx=10, anchor="w")

        # Save Button
        save_btn = ctk.CTkButton(settings_frame, text="Save Settings", command=self.save_settings)
        save_btn.pack(pady=30, padx=10)

    def save_settings(self):
        exclusions = self.exclusion_entry.get()
        keep_count = self.keep_count_entry.get()

        try:
            # Simple .env update
            env_path = ".env"
            lines = []
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    lines = f.readlines()
            
            new_lines = []
            keys_handled = set()
            for line in lines:
                if line.startswith("EXCLUSION_LIST="):
                    new_lines.append(f"EXCLUSION_LIST={exclusions}\n")
                    keys_handled.add("EXCLUSION_LIST")
                elif line.startswith("SAVE_KEEP_COUNT="):
                    new_lines.append(f"SAVE_KEEP_COUNT={keep_count}\n")
                    keys_handled.add("SAVE_KEEP_COUNT")
                else:
                    new_lines.append(line)
            
            if "EXCLUSION_LIST" not in keys_handled:
                new_lines.append(f"EXCLUSION_LIST={exclusions}\n")
            if "SAVE_KEEP_COUNT" not in keys_handled:
                new_lines.append(f"SAVE_KEEP_COUNT={keep_count}\n")

            with open(env_path, "w") as f:
                f.writelines(new_lines)
            
            self.show_info("Settings saved successfully!\nRestart the service to apply changes.")
            load_dotenv() # Reload in current process
        except Exception as e:
            self.show_error(f"Failed to save settings: {e}")

    def load_data(self):
        saves = self.client.get_all_saves()
        
        # Group saves by ROM ID/Name
        self.rom_data = {}
        for save in saves:
            rom_id = save.get("rom_id")
            rom_name = save.get("rom", {}).get("name", f"ROM {rom_id}")
            if rom_id not in self.rom_data:
                self.rom_data[rom_id] = {"name": rom_name, "saves": []}
            self.rom_data[rom_id]["saves"].append(save)

        # Sort saves by date descending
        for rom_id in self.rom_data:
            self.rom_data[rom_id]["saves"].sort(key=lambda x: x.get("added_at", ""), reverse=True)

        # Populate sidebar
        for rom_id, data in self.rom_data.items():
            btn = ctk.CTkButton(self.rom_listbox, text=data["name"], 
                               command=lambda r=rom_id: self.show_versions(r))
            btn.pack(fill="x", pady=5, padx=5)

    def show_versions(self, rom_id):
        self.rom_title.configure(text=self.rom_data[rom_id]["name"])
        
        # Clear version list
        for widget in self.version_list.winfo_children():
            widget.destroy()
            
        for save in self.rom_data[rom_id]["saves"]:
            filename = save.get("name")
            added_at = save.get("added_at", "Unknown Date")
            save_id = save.get("id")
            
            frame = ctk.CTkFrame(self.version_list)
            frame.pack(fill="x", pady=5, padx=5)
            
            label = ctk.CTkLabel(frame, text=f"{filename}\nUploaded: {added_at}", justify="left")
            label.pack(side="left", padx=10, pady=10)
            
            btn = ctk.CTkButton(frame, text="Restore", width=100,
                               command=lambda s=save: self.restore_save(s))
            btn.pack(side="right", padx=10, pady=10)

    def restore_save(self, save_data):
        versioned_name = save_data.get("name")
        save_id = save_data.get("id")
        
        # Remove timestamp: "Game_20231027_123000.srm" -> "Game.srm"
        # Using regex to find _YYYYMMDD_HHMMSS
        clean_name = re.sub(r'_\d{8}_\d{6}', '', versioned_name)
        
        # Try to find where this save should go
        target_dir = None
        for path in self.monitor_paths:
            if os.path.exists(path):
                # Search for an existing file with the same name or just use the first path as a guess
                if os.path.exists(os.path.join(path, clean_name)):
                    target_dir = path
                    break
        
        if not target_dir and self.monitor_paths:
            target_dir = self.monitor_paths[0] # Fallback to first path
            
        if not target_dir:
            self.show_error("Could not determine target directory. Check MONITOR_PATHS.")
            return

        target_path = os.path.join(target_dir, clean_name)
        
        if self.client.download_save(save_id, target_path):
            self.show_info(f"Successfully restored to:\n{target_path}")
        else:
            self.show_error("Failed to download save file.")

    def show_error(self, message):
        from tkinter import messagebox
        messagebox.showerror("Error", message)

    def show_info(self, message):
        from tkinter import messagebox
        messagebox.showinfo("Success", message)

if __name__ == "__main__":
    app = SaveManager()
    app.mainloop()
