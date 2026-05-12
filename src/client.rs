use reqwest::{Client, multipart};
use serde::{Deserialize, Serialize};
use std::path::Path;
use anyhow::Result;
use chrono::Local;
use log::{info, error, warn};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Rom {
    pub id: i32,
    pub name: String,
    pub path: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Save {
    pub id: i32,
    pub name: String,
    pub rom_id: i32,
    pub added_at: String,
    pub rom: Option<Rom>,
}

#[derive(Debug, Deserialize)]
struct RomSearchResponse {
    pub roms: Vec<Rom>,
}

pub struct RomMClient {
    base_url: String,
    client: Client,
    username: Option<String>,
    password: Option<String>,
}

impl RomMClient {
    pub fn new(base_url: &str, username: Option<String>, password: Option<String>) -> Self {
        Self {
            base_url: base_url.trim_end_matches('/').to_string(),
            client: Client::new(),
            username,
            password,
        }
    }

    fn apply_auth(&self, builder: reqwest::RequestBuilder) -> reqwest::RequestBuilder {
        if let (Some(u), Some(p)) = (&self.username, &self.password) {
            builder.basic_auth(u, Some(p))
        } else {
            builder
        }
    }

    pub async fn check_heartbeat(&self) -> bool {
        let url = format!("{}/api/heartbeat", self.base_url);
        match self.client.get(&url).send().await {
            Ok(resp) => resp.status().is_success(),
            Err(e) => {
                error!("Heartbeat failed: {}", e);
                false
            }
        }
    }

    pub async fn upload_save(&self, rom_id: i32, file_path: &Path, emulator: Option<&str>) -> Result<serde_json::Value> {
        let url = format!("{}/api/saves", self.base_url);
        
        let timestamp = Local::now().format("%Y%m%d_%H%M%S").to_string();
        let filename = file_path.file_name().unwrap().to_str().unwrap();
        let stem = file_path.file_stem().unwrap().to_str().unwrap();
        let extension = file_path.extension().unwrap_or_default().to_str().unwrap();
        
        let versioned_filename = if extension.is_empty() {
            format!("{}_{}", stem, timestamp)
        } else {
            format!("{}_{}.{}", stem, timestamp, extension)
        };

        let file_bytes = tokio::fs::read(file_path).await?;
        let part = multipart::Part::bytes(file_bytes)
            .file_name(versioned_filename)
            .mime_str("application/octet-stream")?;

        let mut form = multipart::Form::new()
            .part("file", part)
            .text("rom_id", rom_id.to_string());

        if let Some(emu) = emulator {
            form = form.text("emulator", emu.to_string());
        }

        info!("Uploading save for ROM ID {}...", rom_id);
        let resp = self.apply_auth(self.client.post(&url))
            .multipart(form)
            .send()
            .await?;

        if !resp.status().is_success() {
            let text = resp.text().await?;
            error!("Upload failed: {}", text);
            return Err(anyhow::anyhow!("Upload failed: {}", text));
        }

        Ok(resp.json().await?)
    }

    pub async fn delete_save(&self, save_id: i32) -> Result<()> {
        let url = format!("{}/api/saves/{}", self.base_url, save_id);
        let resp = self.apply_auth(self.client.delete(&url)).send().await?;
        
        if resp.status().is_success() {
            Ok(())
        } else {
            Err(anyhow::anyhow!("Failed to delete save: {}", resp.status()))
        }
    }

    pub async fn get_saves_for_rom(&self, rom_id: i32) -> Result<Vec<Save>> {
        let url = format!("{}/api/saves", self.base_url);
        let resp = self.apply_auth(self.client.get(&url))
            .query(&[("rom_id", rom_id)])
            .send()
            .await?;
            
        Ok(resp.json().await?)
    }

    pub async fn search_rom(&self, search_term: &str) -> Result<Option<i32>> {
        let url = format!("{}/api/roms", self.base_url);
        let resp = self.apply_auth(self.client.get(&url))
            .query(&[("search", search_term), ("page", "1"), ("page_size", "10")])
            .send()
            .await?;

        let data: serde_json::Value = resp.json().await?;
        
        // Handle both {"roms": [...]} and [...] structures
        let roms = if data.is_array() {
            serde_json::from_value::<Vec<Rom>>(data)?
        } else if let Some(arr) = data.get("roms") {
            serde_json::from_value::<Vec<Rom>>(arr.clone())?
        } else {
            return Ok(None);
        };

        if roms.is_empty() {
            return Ok(None);
        }

        // Try exact match
        for rom in &roms {
            if let Some(path) = &rom.path {
                if path.to_lowercase().contains(&search_term.to_lowercase()) {
                    return Ok(Some(rom.id));
                }
            }
            if rom.name.to_lowercase() == search_term.to_lowercase() {
                return Ok(Some(rom.id));
            }
        }

        // Fallback to first
        Ok(Some(roms[0].id))
    }
}
