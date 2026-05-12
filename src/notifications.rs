use std::process::Command;
use log::{warn, error};

pub struct NotificationManager;

impl NotificationManager {
    pub fn send(title: &str, message: &str, icon: Option<&str>, urgency: &str) {
        let mut cmd = Command::new("notify-send");
        cmd.arg(title).arg(message).arg("-u").arg(urgency);

        if let Some(i) = icon {
            cmd.arg("-i").arg(i);
        }

        match cmd.status() {
            Ok(status) => {
                if !status.success() {
                    warn!("notify-send failed with status: {}", status);
                }
            }
            Err(e) => {
                error!("Failed to execute notify-send: {}", e);
            }
        }
    }

    pub fn notify_success(rom_name: &str, filename: &str) {
        Self::send(
            "SteamRomSync",
            &format!("Successfully synced save for {}:\n{}", rom_name, filename),
            Some("emblem-shared"),
            "normal",
        );
    }

    pub fn notify_error(message: &str) {
        Self::send(
            "SteamRomSync Error",
            message,
            Some("dialog-error"),
            "critical",
        );
    }
}
