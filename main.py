from fastapi import FastAPI, HTTPException
import os
import hashlib
from pathlib import Path
from typing import Dict, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

app = FastAPI(title="Directory Monitor Pro")

# Database
dir_db: Dict[str, Dict[str, str]] = {}  # {dir_name: {file_path: hash}}
change_log = []

# File Monitoring Thread
observer = None

class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            filepath = event.src_path
            dir_name = os.path.basename(os.path.dirname(filepath))
            if dir_name in dir_db:
                new_hash = hash_file(filepath)
                if dir_db[dir_name].get(filepath) != new_hash:
                    change_log.append(f"MODIFIED: {filepath}")
                    dir_db[dir_name][filepath] = new_hash

def hash_file(filepath: str) -> str:
    """Generate SHA-256 hash of file content"""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

@app.on_event("startup")
def start_monitoring():
    global observer
    observer = Observer()
    observer.start()

@app.on_event("shutdown")
def stop_monitoring():
    if observer:
        observer.stop()
        observer.join()

@app.post("/register/")
async def register_directory(dir_path: str):
    """Register a directory for monitoring"""
    dir_path = os.path.normpath(dir_path)
    if not os.path.isdir(dir_path):
        raise HTTPException(400, "Invalid directory path")
    
    dir_name = os.path.basename(dir_path)
    dir_db[dir_name] = {}
    
    # Scan all files
    for filepath in Path(dir_path).rglob('*'):
        if filepath.is_file():
            try:
                dir_db[dir_name][str(filepath)] = hash_file(str(filepath))
            except Exception as e:
                print(f"Skipping {filepath}: {e}")
    
    # Start monitoring
    event_handler = ChangeHandler()
    observer.schedule(event_handler, dir_path, recursive=True)
    
    return {
        "status": "success",
        "directory": dir_path,
        "files_registered": len(dir_db[dir_name])
    }

@app.get("/verify/{dir_name}")
def verify_changes(dir_name: str):
    """Check for all types of changes"""
    if dir_name not in dir_db:
        raise HTTPException(404, "Directory not registered")
    
    original = dir_db[dir_name]
    current = {}
    dir_path = next(iter(original)) if original else ""
    dir_path = os.path.dirname(dir_path) if dir_path else ""
    
    # Rescan directory
    for filepath in Path(dir_path).rglob('*'):
        if filepath.is_file():
            try:
                current[str(filepath)] = hash_file(str(filepath))
            except Exception as e:
                print(f"Skipping {filepath}: {e}")
    
    # Compare
    added = [f for f in current if f not in original]
    deleted = [f for f in original if f not in current]
    modified = [f for f in current if f in original and current[f] != original[f]]
    
    # Update database
    dir_db[dir_name] = current
    
    return {
        "directory": dir_path,
        "added": added,
        "deleted": deleted,
        "modified": modified,
        "recent_changes": change_log[-10:]  # Last 10 changes from watchdog
    }

@app.get("/list/{dir_name}")
def list_files(dir_name: str):
    """List all files with details in a registered directory"""
    if dir_name not in dir_db:
        raise HTTPException(404, "Directory not registered")
    
    # Get the actual directory path from stored files
    sample_file = next(iter(dir_db[dir_name].keys()), None)
    dir_path = os.path.dirname(sample_file) if sample_file else ""
    
    if not dir_path:
        return {"error": "No files found in directory"}
    
    file_details = []
    for filepath, filehash in dir_db[dir_name].items():
        try:
            file_stats = os.stat(filepath)
            file_details.append({
                "filename": os.path.basename(filepath),
                "path": filepath,
                "hash": filehash,
                "size_bytes": file_stats.st_size,
                "last_modified": file_stats.st_mtime,
                "is_text": filepath.endswith(('.txt', '.csv', '.json', '.xml'))  # Add more extensions if needed
            })
        except Exception as e:
            print(f"Skipping {filepath}: {str(e)}")
            continue
    
    return {
        "directory": dir_path,
        "total_files": len(file_details),
        "files": sorted(file_details, key=lambda x: x['filename'])
    }
