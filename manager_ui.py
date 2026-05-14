import subprocess
import customtkinter as ctk
import os
import logging
import re
import json
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
from dotenv import load_dotenv, set_key
from romm_client import RomMClient

MAPPINGS_FILE = "mappings.json"

# Configure logging
logging.basicConfig(level=logging.INFO)

class SaveManager(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SteamRomSync Save Manager")
        self.geometry("900x750")
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.load_env_vars()
        self.mappings = self.load_mappings()
        
        self.client = None
        self.init_client()
        
        self.setup_ui()
        if self.client:
            self.load_data()
        
        self.after(1000, self.check_pending_mappings)

    def load_mappings(self):
        if os.path.exists(MAPPINGS_FILE):
            try:
                with open(MAPPINGS_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load mappings: {e}")
        return {}

    def save_mappings(self):
        try:
            with open(MAPPINGS_FILE, "w") as f:
                json.dump(self.mappings, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save mappings: {e}")

    def check_pending_mappings(self):
        pending = [name for name, data in self.mappings.items() if not data.get("confirmed", False)]
        if pending:
            if messagebox.askyesno("Pending Mappings", f"You have {len(pending)} unconfirmed ROM mappings from fuzzy matching.\n\nWould you like to review them now?"):
                self.show_mapping_confirmation()

    def show_mapping_confirmation(self):
        # Create a scrollable window for reviewing mappings
        top = ctk.CTkToplevel(self)
        top.title("Review Fuzzy Mappings")
        top.geometry("700x500")
        top.attributes("-topmost", True)
        
        ctk.CTkLabel(top, text="Review Fuzzy Mappings", font=("Helvetica", 18, "bold")).pack(pady=10)
        ctk.CTkLabel(top, text="The following ROMs were matched using fuzzy logic. Please confirm if they are correct.").pack(pady=5)
        
        frame = ctk.CTkScrollableFrame(top)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        pending_data = {name: data for name, data in self.mappings.items() if not data.get("confirmed", False)}
        
        if not pending_data:
            ctk.CTkLabel(frame, text="No pending mappings!").pack(pady=20)
            return

        for local_name, data in pending_data.items():
            row = ctk.CTkFrame(frame)
            row.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(row, text=f"Local: {local_name}", width=200, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text="→", width=20).pack(side="left")
            ctk.CTkLabel(row, text=f"RomM: {data['matched_name']} ({data['score']}%)", width=250, anchor="w").pack(side="left", padx=5)
            
            btn_confirm = ctk.CTkButton(row, text="Confirm", width=80, fg_color="green", 
                                       command=lambda n=local_name, t=top: self.confirm_mapping(n, t))
            btn_confirm.pack(side="right", padx=2)
            
            btn_fix = ctk.CTkButton(row, text="Fix", width=60, fg_color="orange", 
                                   command=lambda n=local_name, t=top: self.fix_mapping(n, t))
            btn_fix.pack(side="right", padx=2)

    def confirm_mapping(self, local_name, top_window):
        if local_name in self.mappings:
            self.mappings[local_name]["confirmed"] = True
            self.save_mappings()
            top_window.destroy()
            self.show_mapping_confirmation()

    def fix_mapping(self, local_name, top_window):
        new_id = simpledialog.askstring("Fix Mapping", f"Enter the correct RomM ID for '{local_name}':", parent=top_window)
        if new_id:
            try:
                self.mappings[local_name] = {
                    "rom_id": int(new_id),
                    "matched_name": "Manually Assigned",
                    "score": 100,
                    "confirmed": True
                }
                self.save_mappings()
                top_window.destroy()
                self.show_mapping_confirmation()
            except ValueError:
                messagebox.showerror("Error", "ID must be a number.", parent=top_window)

    def load_env_vars(self):
        load_dotenv(override=True)
        self.romm_url = os.getenv("ROMM_URL")
        self.romm_api_key = os.getenv("ROMM_API_KEY")
        self.romm_username = os.getenv("ROMM_USERNAME")
        self.romm_password = os.getenv("ROMM_PASSWORD")
        self.monitor_paths = [p.strip() for p in os.getenv("MONITOR_PATHS", "").split(",") if p.strip()]

    def init_client(self):
        if self.romm_url:
            self.client = RomMClient(self.romm_url, api_key=self.romm_api_key, username=self.romm_username, password=self.romm_password)
        else:
            self.client = None

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
        
        if not self.romm_url:
            self.show_settings_view()
        else:
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

        # --- RomM Connection Settings ---
        ctk.CTkLabel(settings_frame, text="RomM Connection", font=("Helvetica", 16, "bold")).pack(pady=(10, 5), padx=10, anchor="w")
        
        # Login Status Area
        status_frame = ctk.CTkFrame(settings_frame)
        status_frame.pack(fill="x", pady=5, padx=10)
        
        self.login_status_label = ctk.CTkLabel(status_frame, text="Checking login status...", font=("Helvetica", 12))
        self.login_status_label.pack(pady=5, padx=10, side="left")
        
        btn_check_login = ctk.CTkButton(status_frame, text="Check Status", command=self.update_login_status, width=100, height=24)
        btn_check_login.pack(pady=5, padx=10, side="right")

        # URL
        ctk.CTkLabel(settings_frame, text="RomM URL", font=("Helvetica", 12)).pack(pady=(10, 0), padx=10, anchor="w")
        self.url_entry = ctk.CTkEntry(settings_frame, width=500)
        self.url_entry.insert(0, self.romm_url or "")
        self.url_entry.pack(pady=5, padx=10, fill="x")

        # API Key
        ctk.CTkLabel(settings_frame, text="API Key (Bearer Token)", font=("Helvetica", 12)).pack(pady=(10, 0), padx=10, anchor="w")
        self.api_key_entry = ctk.CTkEntry(settings_frame, width=500, show="*")
        self.api_key_entry.insert(0, self.romm_api_key or "")
        self.api_key_entry.pack(pady=5, padx=10, fill="x")

        # Username
        ctk.CTkLabel(settings_frame, text="Username", font=("Helvetica", 12)).pack(pady=(10, 0), padx=10, anchor="w")
        self.user_entry = ctk.CTkEntry(settings_frame, width=500)
        self.user_entry.insert(0, self.romm_username or "")
        self.user_entry.pack(pady=5, padx=10, fill="x")

        # Password
        ctk.CTkLabel(settings_frame, text="Password", font=("Helvetica", 12)).pack(pady=(10, 0), padx=10, anchor="w")
        self.pass_entry = ctk.CTkEntry(settings_frame, width=500, show="*")
        self.pass_entry.insert(0, self.romm_password or "")
        self.pass_entry.pack(pady=5, padx=10, fill="x")

        # --- Monitor Paths ---
        ctk.CTkLabel(settings_frame, text="Monitor Paths", font=("Helvetica", 16, "bold")).pack(pady=(20, 5), padx=10, anchor="w")
        
        path_mgr_frame = ctk.CTkFrame(settings_frame)
        path_mgr_frame.pack(fill="x", pady=5, padx=10)
        
        self.path_listbox = ctk.CTkTextbox(path_mgr_frame, height=100)
        self.path_listbox.pack(fill="x", padx=10, pady=10)
        self.refresh_path_list()

        path_btn_frame = ctk.CTkFrame(path_mgr_frame, fg_color="transparent")
        path_btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        btn_add_path = ctk.CTkButton(path_btn_frame, text="Add Path", command=self.add_path, width=100)
        btn_add_path.pack(side="left", padx=5)
        
        btn_clear_paths = ctk.CTkButton(path_btn_frame, text="Clear All", command=self.clear_paths, width=100, fg_color="red")
        btn_clear_paths.pack(side="left", padx=5)

        btn_view_local = ctk.CTkButton(path_btn_frame, text="View Discovered Files", command=self.view_local_saves, width=150, fg_color="green")
        btn_view_local.pack(side="left", padx=5)

        # --- Service Management ---
        ctk.CTkLabel(settings_frame, text="Service Management", font=("Helvetica", 16, "bold")).pack(pady=(20, 5), padx=10, anchor="w")
        
        status_frame_svc = ctk.CTkFrame(settings_frame)
        status_frame_svc.pack(fill="x", pady=5, padx=10)
        
        self.service_status_label = ctk.CTkLabel(status_frame_svc, text="Checking status...", font=("Helvetica", 12))
        self.service_status_label.pack(pady=5, padx=10, anchor="w")
        
        btn_frame_svc = ctk.CTkFrame(status_frame_svc, fg_color="transparent")
        btn_frame_svc.pack(fill="x", pady=5, padx=10)
        
        self.btn_restart = ctk.CTkButton(btn_frame_svc, text="Restart Service", command=self.restart_service, width=150)
        self.btn_restart.pack(side="left", padx=5)
        
        self.btn_refresh_status = ctk.CTkButton(btn_frame_svc, text="Refresh Status", command=self.update_service_status, width=150, fg_color="gray")
        self.btn_refresh_status.pack(side="left", padx=5)

        # Exclusion List
        ctk.CTkLabel(settings_frame, text="Exclusion List (Comma separated names/paths)", font=("Helvetica", 14, "bold")).pack(pady=(20, 5), padx=10, anchor="w")
        self.exclusion_entry = ctk.CTkEntry(settings_frame, width=500)
        self.exclusion_entry.insert(0, os.getenv("EXCLUSION_LIST", ""))
        self.exclusion_entry.pack(pady=5, padx=10, fill="x")

        # Save Keep Count
        ctk.CTkLabel(settings_frame, text="Save Versions to Keep (0 = Unlimited)", font=("Helvetica", 14, "bold")).pack(pady=(20, 5), padx=10, anchor="w")
        self.keep_count_entry = ctk.CTkEntry(settings_frame, width=100)
        self.keep_count_entry.insert(0, os.getenv("SAVE_KEEP_COUNT", "0"))
        self.keep_count_entry.pack(pady=5, padx=10, anchor="w")

        # Save Button
        save_btn = ctk.CTkButton(settings_frame, text="Save All Settings", command=self.save_settings, height=40, font=("Helvetica", 14, "bold"))
        save_btn.pack(pady=40, padx=10)
        
        # Initial status updates
        self.update_service_status()
        self.update_login_status()

    def refresh_path_list(self):
        self.path_listbox.configure(state="normal")
        self.path_listbox.delete("1.0", "end")
        self.path_listbox.insert("1.0", "\n".join(self.monitor_paths))
        self.path_listbox.configure(state="disabled")

    def add_path(self):
        path = filedialog.askdirectory()
        if path:
            if path not in self.monitor_paths:
                self.monitor_paths.append(path)
                self.refresh_path_list()

    def clear_paths(self):
        if messagebox.askyesno("Clear Paths", "Are you sure you want to clear all monitor paths?"):
            self.monitor_paths = []
            self.refresh_path_list()

    def view_local_saves(self):
        from discovery import discover_save_files
        files = discover_save_files(self.monitor_paths)
        if not files:
            messagebox.showinfo("Discovered Files", "No save files found in the monitored paths.")
            return
        
        # Create a scrollable window to show files
        top = ctk.CTkToplevel(self)
        top.title("Discovered Local Save Files")
        top.geometry("700x500")
        
        frame = ctk.CTkScrollableFrame(top)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        for file in files:
            ctk.CTkLabel(frame, text=file, anchor="w").pack(fill="x", pady=2)

    def update_login_status(self):
        if not self.client:
            self.login_status_label.configure(text="● Status: Not Configured", text_color="gray")
            return

        if self.client.check_heartbeat():
            self.login_status_label.configure(text="● Status: Logged In", text_color="green")
        else:
            self.login_status_label.configure(text="○ Status: Connection Failed", text_color="red")

    def update_service_status(self):
        """Checks the status of the systemd user service."""
        try:
            result = subprocess.run(["systemctl", "--user", "is-active", "steamromsync.service"], capture_output=True, text=True)
            status = result.stdout.strip()
            
            if status == "active":
                self.service_status_label.configure(text="● SteamRomSync Service: Active", text_color="green")
            else:
                self.service_status_label.configure(text=f"○ SteamRomSync Service: {status.capitalize() or 'Inactive'}", text_color="red")
        except Exception as e:
            self.service_status_label.configure(text=f"Service status error: {e}", text_color="orange")

    def restart_service(self):
        """Restarts the systemd user service."""
        try:
            self.service_status_label.configure(text="Restarting...", text_color="yellow")
            subprocess.run(["systemctl", "--user", "restart", "steamromsync.service"], check=True)
            self.update_service_status()
            messagebox.showinfo("Success", "Service restarted successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart service: {e}")
            self.update_service_status()

    def save_settings(self):
        url = self.url_entry.get()
        api_key = self.api_key_entry.get()
        user = self.user_entry.get()
        password = self.pass_entry.get()
        paths = ",".join(self.monitor_paths)
        exclusions = self.exclusion_entry.get()
        keep_count = self.keep_count_entry.get()

        try:
            env_path = ".env"
            # Ensure .env exists
            if not os.path.exists(env_path):
                open(env_path, 'a').close()

            set_key(env_path, "ROMM_URL", url)
            set_key(env_path, "ROMM_API_KEY", api_key)
            set_key(env_path, "ROMM_USERNAME", user)
            set_key(env_path, "ROMM_PASSWORD", password)
            set_key(env_path, "MONITOR_PATHS", paths)
            set_key(env_path, "EXCLUSION_LIST", exclusions)
            set_key(env_path, "SAVE_KEEP_COUNT", keep_count)
            
            self.load_env_vars()
            self.init_client()
            self.update_login_status()
            
            messagebox.showinfo("Success", "Settings saved successfully!\nRestart the service to apply changes.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def load_data(self):
        if not self.client:
            return

        try:
            saves = self.client.get_all_saves()
            
            # Clear sidebar
            for widget in self.rom_listbox.winfo_children():
                widget.destroy()

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
        except Exception as e:
            logging.error(f"Failed to load data: {e}")

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
        clean_name = re.sub(r'_\d{8}_\d{6}', '', versioned_name)
        
        # Try to find where this save should go
        target_dir = None
        for path in self.monitor_paths:
            if os.path.exists(path):
                if os.path.exists(os.path.join(path, clean_name)):
                    target_dir = path
                    break
        
        if not target_dir and self.monitor_paths:
            target_dir = self.monitor_paths[0] # Fallback to first path
            
        if not target_dir:
            messagebox.showerror("Error", "Could not determine target directory. Check MONITOR_PATHS.")
            return

        target_path = os.path.join(target_dir, clean_name)
        
        if self.client.download_save(save_id, target_path):
            messagebox.showinfo("Success", f"Successfully restored to:\n{target_path}")
        else:
            messagebox.showerror("Error", "Failed to download save file.")

if __name__ == "__main__":
    app = SaveManager()
    app.mainloop()
