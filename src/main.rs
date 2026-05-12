mod client;
mod manager;
mod watcher;
mod notifications;
mod discovery;

use std::env;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::Mutex;
use dotenvy::dotenv;
use log::{info, error};
use crate::client::RomMClient;
use crate::manager::SyncManager;
use crate::watcher::SaveWatcher;
use crate::discovery::discover_save_files;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    env_logger::init_from_env(env_logger::Env::default().default_filter_or("info"));
    
    dotenv().ok();

    let romm_url = env::var("ROMM_URL").expect("ROMM_URL must be set");
    let romm_username = env::var("ROMM_USERNAME").ok();
    let romm_password = env::var("ROMM_PASSWORD").ok();
    
    let monitor_paths_raw = env::var("MONITOR_PATHS").unwrap_or_default();
    let monitor_paths: Vec<PathBuf> = monitor_paths_raw
        .split(',')
        .filter(|s| !s.is_empty())
        .map(PathBuf::from)
        .collect();

    let exclusion_list_raw = env::var("EXCLUSION_LIST").unwrap_or_default();
    let exclusion_list: Vec<String> = exclusion_list_raw
        .split(',')
        .filter(|s| !s.is_empty())
        .map(|s| s.trim().to_string())
        .collect();

    let save_keep_count: i32 = env::var("SAVE_KEEP_COUNT")
        .unwrap_or_else(|_| "0".to_string())
        .parse()
        .unwrap_or(0);

    info!("Starting SteamRomSync (Rust)...");

    let client = RomMClient::new(&romm_url, romm_username, romm_password);
    
    if !client.check_heartbeat().await {
        info!("Warning: Could not reach RomM heartbeat.");
    }

    let manager = SyncManager::new(
        client,
        monitor_paths.clone(),
        exclusion_list,
        save_keep_count,
    );
    
    let manager_shared = Arc::new(Mutex::new(manager));

    // Initial scan
    info!("Performing initial save discovery and backup...");
    let files = discover_save_files(&monitor_paths);
    let mut mgr = manager_shared.lock().await;
    for file in files {
        if let Err(e) = mgr.handle_save_change(&file).await {
            error!("Initial scan error for {:?}: {}", file, e);
        }
    }
    drop(mgr);

    let watcher = SaveWatcher::new(monitor_paths);
    watcher.start(manager_shared).await?;

    Ok(())
}
