import subprocess
import logging
import os

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
        NotificationManager.send(
            "SteamRomSync", 
            f"Successfully synced save for {rom_name}:\n{filename}",
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
