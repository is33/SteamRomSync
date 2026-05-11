import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SaveEventHandler(FileSystemEventHandler):
    def __init__(self, callback, debounce_seconds=5):
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.last_events = {}

    def on_modified(self, event):
        if event.is_directory:
            return
        
        current_time = time.time()
        file_path = event.src_path
        
        # Debounce logic
        if file_path in self.last_events:
            if current_time - self.last_events[file_path] < self.debounce_seconds:
                return
        
        self.last_events[file_path] = current_time
        logging.info(f"Detected modification: {file_path}")
        self.callback(file_path)

class SaveWatcher:
    def __init__(self, paths, callback):
        self.paths = paths
        self.callback = callback
        self.observer = Observer()

    def start(self):
        event_handler = SaveEventHandler(self.callback)
        for path in self.paths:
            logging.info(f"Watching path: {path}")
            self.observer.schedule(event_handler, path, recursive=True)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()
