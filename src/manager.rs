use std::path::{Path, PathBuf};
use std::collections::HashMap;
use anyhow::Result;
use log::{info, warn, error, debug};
use crate::client::RomMClient;
use crate::notifications::NotificationManager;

pub struct SyncManager {
    client: RomMClient,
    monitor_paths: Vec<PathBuf>,
    exclusion_list: Vec<String>,
    save_keep_count: i32,
    rom_id_cache: HashMap<String, i32>,
    last_sync_times: HashMap<PathBuf, std::time::SystemTime>,
}

impl SyncManager {
    pub fn new(
        client: RomMClient,
        monitor_paths: Vec<PathBuf>,
        exclusion_list: Vec<String>,
        save_keep_count: i32,
    ) -> Self {
        Self {
            client,
            monitor_paths,
            exclusion_list,
            save_keep_count,
            rom_id_cache: HashMap::new(),
            last_sync_times: HashMap::new(),
        }
    }

    pub fn is_excluded(&self, path: &Path) -> bool {
        let path_str = path.to_string_lossy().to_lowercase();
        let filename = path.file_name().unwrap_or_default().to_string_lossy().to_lowercase();
        
        for exclusion in &self.exclusion_list {
            let exc_lower = exclusion.to_lowercase();
            if path_str.contains(&exc_lower) || filename.contains(&exc_lower) {
                return true;
            }
        }
        false
    }

    pub async fn handle_save_change(&mut self, path: &Path) -> Result<()> {
        if self.is_excluded(path) {
            debug!("Skipping excluded path: {:?}", path);
            return Ok(());
        }

        let filename = path.file_name().unwrap().to_string_lossy();
        let extension = path.extension().and_then(|e| e.to_str()).unwrap_or_default().to_lowercase();

        let save_extensions = [
            "srm", "sav", "state", "bsv", "nvram", "ups", "ips",
            "ps2", "gci", "raw", "vmp", "mcd"
        ];

        let path_str = path.to_string_lossy();
        let is_vita = path_str.contains("savedata") && path_str.contains("Vita3K");

        if !is_vita && !save_extensions.contains(&extension.as_str()) {
            return Ok(());
        }

        let rom_name = self.detect_rom_name(path, &filename, is_vita);
        info!("Syncing save for: {}", rom_name);

        let rom_id = self.get_rom_id(&rom_name).await?;

        if let Some(id) = rom_id {
            match self.client.upload_save(id, path, None).await {
                Ok(_) => {
                    info!("Successfully uploaded save for {} (ID: {})", rom_name, id);
                    
                    if self.save_keep_count > 0 {
                        self.perform_cleanup(id).await?;
                    }

                    NotificationManager.notify_success(&rom_name, &filename);
                }
                Err(e) => {
                    error!("Failed to upload save for {}: {}", rom_name, e);
                    NotificationManager.notify_error(&format!("Failed to sync {}: {}", rom_name, e));
                }
            }
        } else {
            warn!("Could not find ROM ID for {}. Skipping.", rom_name);
        }

        Ok(())
    }

    fn detect_rom_name(&self, path: &Path, filename: &str, is_vita: bool) -> String {
        if is_vita {
            let components: Vec<_> = path.components().collect();
            for (i, comp) in components.iter().enumerate() {
                if comp.as_os_str() == "savedata" && i + 1 < components.len() {
                    return components[i+1].as_os_str().to_string_lossy().to_string();
                }
            }
        }
        
        path.file_stem().unwrap().to_string_lossy().to_string()
    }

    async fn perform_cleanup(&self, rom_id: i32) -> Result<()> {
        let mut saves = self.client.get_saves_for_rom(rom_id).await?;
        if saves.len() > self.save_keep_count as usize {
            // Sort by added_at descending
            saves.sort_by(|a, b| b.added_at.cmp(&a.added_at));
            
            let to_delete = &saves[self.save_keep_count as usize..];
            for save in to_delete {
                if let Err(e) = self.client.delete_save(save.id).await {
                    error!("Failed to delete old save {}: {}", save.id, e);
                }
            }
            info!("Cleaned up {} old save versions for ROM ID {}", to_delete.len(), rom_id);
        }
        Ok(())
    }

    async fn get_rom_id(&mut self, rom_name: &str) -> Result<Option<i32>> {
        if let Some(id) = self.rom_id_cache.get(rom_name) {
            return Ok(Some(*id));
        }

        if let Some(id) = self.client.search_rom(rom_name).await? {
            self.rom_id_cache.insert(rom_name.to_string(), id);
            Ok(Some(id))
        } else {
            Ok(None)
        }
    }
}
