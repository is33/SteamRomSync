use notify::{Watcher, RecursiveMode, Config, RecommendedWatcher, Event};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::sync::Mutex;
use log::{info, error, debug};
use crate::manager::SyncManager;

pub struct SaveWatcher {
    paths: Vec<PathBuf>,
}

impl SaveWatcher {
    pub fn new(paths: Vec<PathBuf>) -> Self {
        Self { paths }
    }

    pub async fn start(self, manager: Arc<Mutex<SyncManager>>) -> anyhow::Result<()> {
        let (tx, mut rx) = tokio::sync::mpsc::channel(100);

        let mut watcher = RecommendedWatcher::new(move |res: notify::Result<Event>| {
            if let Ok(event) = res {
                if event.kind.is_modify() || event.kind.is_create() {
                    for path in event.paths {
                        let _ = tx.blocking_send(path);
                    }
                }
            }
        }, Config::default())?;

        for path in &self.paths {
            if path.exists() {
                watcher.watch(path, RecursiveMode::Recursive)?;
                info!("Watching path: {:?}", path);
            }
        }

        info!("Watcher started...");

        while let Some(path) = rx.recv().await {
            let mut mgr = manager.lock().await;
            if let Err(e) = mgr.handle_save_change(&path).await {
                error!("Error handling file change for {:?}: {}", path, e);
            }
        }

        Ok(())
    }
}
