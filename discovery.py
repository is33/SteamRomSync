import os
import glob
from pathlib import Path

# Well-known EmuDeck save locations (Internal and SD Card)
DEFAULT_BASE_PATHS = [
    "/home/deck/Emulation/saves",
    "/home/deck/Emulation/storage",
    "/home/deck/.var/app/org.libretro.RetroArch/config/retroarch/saves",
    "/home/deck/.var/app/org.libretro.RetroArch/config/retroarch/states",
    "/home/deck/.var/app/org.dolphin_emu.dolphin/data/dolphin-emu/GC",
    "/home/deck/.var/app/net.pcsx2.PCSX2/config/PCSX2/memcards",
    "/home/deck/.var/app/org.ppsspp.PPSSPP/config/ppsspp/PSP/SAVEDATA",
    "/home/deck/.var/app/org.citra_emu.citra/data/citra-emu/sdmc",
    "/home/deck/.var/app/org.duckstation.DuckStation/config/duckstation/memcards",
    "/home/deck/.var/app/net.rpcs3.RPCS3/config/rpcs3/dev_hdd0/home/00000001/savedata",
    "/home/deck/.var/app/org.yuzu_emu.yuzu/data/yuzu/nand/system/save",
    "/run/media/mmcblk0p1/Emulation/saves",
    "/run/media/mmcblk0p1/Emulation/storage",
]

SAVE_EXTENSIONS = {
    '.srm', '.sav', '.state', '.bsv', '.nvram', '.ups', '.ips', 
    '.mcd', '.mcr', '.gme', '.psx', '.vme', '.mem'
}

def discover_save_files(extra_paths=None):
    """Discovers all save files in well-known locations."""
    search_paths = DEFAULT_BASE_PATHS.copy()
    if extra_paths:
        search_paths.extend(extra_paths)
    
    found_files = []
    for base_path in search_paths:
        if not os.path.exists(base_path):
            continue
            
        # Walk recursively
        for root, dirs, files in os.walk(base_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in SAVE_EXTENSIONS or "Vita3K" in root:
                    full_path = os.path.join(root, file)
                    found_files.append(full_path)
                    
    return found_files
