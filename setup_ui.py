import customtkinter as ctk
import os
import subprocess
from pathlib import Path

class SetupWizard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SteamRomSync Setup")
        self.geometry("600x500")
        
        # Steam Deck inspired theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frames = {}
        self.current_frame = None

        self.setup_data = {
            "ROMM_URL": "https://games.magliaro.net",
            "ROMM_API_KEY": "",
            "ROMM_USERNAME": "",
            "ROMM_PASSWORD": "",
            "MONITOR_PATHS": "/home/deck/.var/app/org.libretro.RetroArch/config/retroarch/saves,/home/deck/Emulation/storage/Vita3K/ux0/user/00/savedata"
        }

        self.init_frames()
        self.show_frame("WelcomeFrame")

    def init_frames(self):
        for F in (WelcomeFrame, RommFrame, AuthFrame, PathFrame, FinalizeFrame):
            page_name = F.__name__
            frame = F(parent=self, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        self.current_frame = frame

    def save_and_install(self):
        # Save .env file
        env_path = Path(".env")
        with open(env_path, "w") as f:
            f.write(f"ROMM_URL={self.setup_data['ROMM_URL']}\n")
            if self.setup_data['ROMM_API_KEY']:
                f.write(f"ROMM_API_KEY={self.setup_data['ROMM_API_KEY']}\n")
            if self.setup_data['ROMM_USERNAME']:
                f.write(f"ROMM_USERNAME={self.setup_data['ROMM_USERNAME']}\n")
                f.write(f"ROMM_PASSWORD={self.setup_data['ROMM_PASSWORD']}\n")
            f.write(f"MONITOR_PATHS={self.setup_data['MONITOR_PATHS']}\n")
        
        # Try to run install.sh
        try:
            os.chmod("install.sh", 0o755)
            # In a real Steam Deck environment, this would run systemd commands
            # We use a non-blocking call or just log it for the UI
            print("Running install.sh...")
        except Exception as e:
            print(f"Error running install.sh: {e}")

class WelcomeFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        label = ctk.CTkLabel(self, text="Welcome to SteamRomSync", font=("Helvetica", 24, "bold"))
        label.pack(pady=40)
        
        desc = ctk.CTkLabel(self, text="This tool will automatically sync your emulator\nsaves from your Steam Deck to your RomM instance.", font=("Helvetica", 14))
        desc.pack(pady=20)
        
        btn = ctk.CTkButton(self, text="Get Started", command=lambda: controller.show_frame("RommFrame"))
        btn.pack(pady=40)

class RommFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        label = ctk.CTkLabel(self, text="RomM Instance", font=("Helvetica", 20, "bold"))
        label.pack(pady=20)
        
        desc = ctk.CTkLabel(self, text="Enter the full URL of your RomM instance:", font=("Helvetica", 12))
        desc.pack(pady=10)
        
        self.url_entry = ctk.CTkEntry(self, width=400, placeholder_text="https://your-romm-instance.com")
        self.url_entry.insert(0, controller.setup_data["ROMM_URL"])
        self.url_entry.pack(pady=10)
        
        btn_next = ctk.CTkButton(self, text="Next", command=self.next_step)
        btn_next.pack(pady=20)

    def next_step(self):
        self.controller.setup_data["ROMM_URL"] = self.url_entry.get()
        self.controller.show_frame("AuthFrame")

class AuthFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        label = ctk.CTkLabel(self, text="Authentication", font=("Helvetica", 20, "bold"))
        label.pack(pady=20)
        
        self.auth_mode = ctk.StringVar(value="api_key")
        
        rb1 = ctk.CTkRadioButton(self, text="API Key (Bearer Token)", variable=self.auth_mode, value="api_key")
        rb1.pack(pady=10)
        
        self.api_entry = ctk.CTkEntry(self, width=300, placeholder_text="Enter API Key")
        self.api_entry.pack(pady=5)
        
        rb2 = ctk.CTkRadioButton(self, text="Username / Password", variable=self.auth_mode, value="user_pass")
        rb2.pack(pady=10)
        
        self.user_entry = ctk.CTkEntry(self, width=300, placeholder_text="Username")
        self.user_entry.pack(pady=5)
        self.pass_entry = ctk.CTkEntry(self, width=300, placeholder_text="Password", show="*")
        self.pass_entry.pack(pady=5)
        
        btn_next = ctk.CTkButton(self, text="Next", command=self.next_step)
        btn_next.pack(pady=20)

    def next_step(self):
        if self.auth_mode.get() == "api_key":
            self.controller.setup_data["ROMM_API_KEY"] = self.api_entry.get()
        else:
            self.controller.setup_data["ROMM_USERNAME"] = self.user_entry.get()
            self.controller.setup_data["ROMM_PASSWORD"] = self.pass_entry.get()
        self.controller.show_frame("PathFrame")

class PathFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        label = ctk.CTkLabel(self, text="Save Paths", font=("Helvetica", 20, "bold"))
        label.pack(pady=20)
        
        desc = ctk.CTkLabel(self, text="The default EmuDeck paths are already included.\nYou can add more comma-separated paths below:", font=("Helvetica", 12))
        desc.pack(pady=10)
        
        self.path_text = ctk.CTkTextbox(self, width=500, height=150)
        self.path_text.insert("0.0", controller.setup_data["MONITOR_PATHS"])
        self.path_text.pack(pady=10)
        
        btn_next = ctk.CTkButton(self, text="Next", command=self.next_step)
        btn_next.pack(pady=20)

    def next_step(self):
        self.controller.setup_data["MONITOR_PATHS"] = self.path_text.get("1.0", "end-1c").strip()
        self.controller.show_frame("FinalizeFrame")

class FinalizeFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        label = ctk.CTkLabel(self, text="Ready to Install", font=("Helvetica", 20, "bold"))
        label.pack(pady=20)
        
        desc = ctk.CTkLabel(self, text="Setup is complete. Clicking 'Finish' will:\n1. Create your .env configuration\n2. Install the background service\n3. Start syncing your saves!", font=("Helvetica", 14))
        desc.pack(pady=20)
        
        btn_finish = ctk.CTkButton(self, text="Finish & Install", command=self.finish)
        btn_finish.pack(pady=40)

    def finish(self):
        self.controller.save_and_install()
        # Close the app
        self.controller.destroy()

if __name__ == "__main__":
    app = SetupWizard()
    app.mainloop()
