use std::path::{Path, PathBuf};
use walkdir::WalkDir;

pub fn discover_save_files(monitor_paths: &[PathBuf]) -> Vec<PathBuf> {
    let mut save_files = Vec::new();
    let save_extensions = [
        "srm", "sav", "state", "bsv", "nvram", "ups", "ips",
        "ps2", "gci", "raw", "vmp", "mcd"
    ];

    for path in monitor_paths {
        if !path.exists() {
            continue;
        }

        for entry in WalkDir::new(path).into_iter().filter_map(|e| e.ok()) {
            if entry.file_type().is_file() {
                let extension = entry.path().extension().and_then(|e| e.to_str()).unwrap_or_default().to_lowercase();
                let path_str = entry.path().to_string_lossy();
                let is_vita = path_str.contains("savedata") && path_str.contains("Vita3K");

                if is_vita || save_extensions.contains(&extension.as_str()) {
                    save_files.push(entry.path().to_path_buf());
                }
            }
        }
    }
    save_files
}
