import subprocess
import logging
import os
import requests

class NotificationManager:
    @staticmethod
    def send(title, message, icon=None, urgency="normal"):
        """Sends a desktop notification using notify-send."""
        try:
            # Check if notify-send exists
            if subprocess.run(["which", "notify-send"], capture_output=True).returncode != 0:
                logging.warning("notify-send not found. Skipping notification.")
                return False

            cmd = ["notify-send", title, message, "-u", urgency]
            
            # Add icon if provided and exists
            if icon and os.path.exists(icon):
                cmd.extend(["-i", icon])
            elif icon:
                # Could be a themed icon name
                cmd.extend(["-i", icon])

            subprocess.run(cmd, check=True)
            return True
        except Exception as e:
            logging.error(f"Failed to send notification: {e}")
            return False

    @staticmethod
    def notify_success(rom_name, filename):
        """Standard success notification for a sync."""
        message = "Successfully synced save for " + rom_name + ":
" + filename
        NotificationManager.send(
            "SteamRomSync", 
            message,
            icon="emblem-shared"
        )

    @staticmethod
    def notify_error(message):
        """Standard error notification."""
        NotificationManager.send(
            "SteamRomSync Error", 
            message,
            urgency="critical",
            icon="dialog-error"
        )
    
    @staticmethod
    def report_error_to_github(error_msg, context):
        """Reports a persistent error to the GitHub repository as an issue."""
        token = os.getenv("GITHUB_PAT")
        repo = os.getenv("GITHUB_REPO")
        if not token or not repo:
            logging.info("GitHub reporting not configured. Skipping.")
            return
        
        url = f"https://api.github.com/repos/{repo}/issues"
        headers = {"Authorization": f"token {token}"}
        
        body = "Sync Error:

" + error_msg + "

Context:
" + context + "

Please check logs for more details."
        
        payload = {
            "title": "Automated Sync Error",
            "body": body
        }
        try:
            requests.post(url, headers=headers, json=payload, timeout=10)
            logging.info("Reported error to GitHub.")
        except Exception as e:
            logging.error(f"Failed to report error to GitHub: {e}")
