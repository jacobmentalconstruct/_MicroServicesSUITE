import os
import shutil
import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Optional

class LibrarianMS:
    """
    The Librarian: Manages the physical creation, deletion, and listing
    of Knowledge Base (KB) files.
    """
    
    def __init__(self, storage_dir: str = "./cortex_dbs"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def list_kbs(self) -> List[str]:
        """
        Scans the storage directory for .db files.
        Equivalent to api.listKBs() in Sidebar.tsx.
        """
        if not self.storage_dir.exists():
            return []
        
        # Return simple filenames sorted by modification time (newest first)
        files = list(self.storage_dir.glob("*.db"))
        files.sort(key=os.path.getmtime, reverse=True)
        return [f.name for f in files]

    def create_kb(self, name: str) -> Dict[str, str]:
        """
        Creates a new SQLite database and initializes the Cortex Schema.
        """
        safe_name = self._sanitize_name(name)
        db_path = self.storage_dir / safe_name
        
        if db_path.exists():
            raise FileExistsError(f"Knowledge Base '{safe_name}' already exists.")

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # --- THE CORTEX SCHEMA ---
            # 1. System Config: Stores version and global metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # 2. Files: Tracks scanned files to avoid re-ingesting unchanged ones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    checksum TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'indexed'
                )
            """)
            
            # 3. Chunks: The actual atomic units of knowledge
            # Note: 'embedding' is stored as a BLOB (bytes) for raw vector data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER,
                    chunk_index INTEGER,
                    content TEXT,
                    embedding BLOB, 
                    FOREIGN KEY(file_id) REFERENCES files(id)
                )
            """)
            
            # 4. Graph Nodes: For the GraphView visualization
            # Distinguishes between 'file' nodes and 'concept' nodes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS graph_nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT,  -- 'file' or 'concept'
                    label TEXT,
                    data_json TEXT -- Flexible JSON for positions/colors
                )
            """)
            
            # 5. Graph Edges: The connections
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS graph_edges (
                    source TEXT,
                    target TEXT,
                    weight REAL DEFAULT 1.0,
                    FOREIGN KEY(source) REFERENCES graph_nodes(id),
                    FOREIGN KEY(target) REFERENCES graph_nodes(id)
                )
            """)
            
            # Timestamp creation
            cursor.execute("INSERT INTO config (key, value) VALUES (?, ?)", 
                           ("created_at", str(time.time())))
            
            conn.commit()
            conn.close()
            return {"status": "success", "path": str(db_path), "name": safe_name}
            
        except Exception as e:
            # Cleanup on failure
            if db_path.exists():
                os.remove(db_path)
            raise e

    def delete_kb(self, name: str) -> bool:
        """
        Physically removes the database file.
        """
        safe_name = self._sanitize_name(name)
        db_path = self.storage_dir / safe_name
        
        if db_path.exists():
            os.remove(db_path)
            return True
        return False

    def duplicate_kb(self, source_name: str) -> Dict[str, str]:
        """
        Creates a copy of an existing KB.
        """
        safe_source = self._sanitize_name(source_name)
        source_path = self.storage_dir / safe_source
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source KB '{safe_source}' not found.")
            
        # Generate new name
        base = safe_source.replace('.db', '')
        new_name = f"{base}_copy.db"
        dest_path = self.storage_dir / new_name
        
        # Handle collision if copy already exists
        counter = 1
        while dest_path.exists():
            new_name = f"{base}_copy_{counter}.db"
            dest_path = self.storage_dir / new_name
            counter += 1
            
        shutil.copy2(source_path, dest_path)
        return {"status": "success", "name": new_name}

    def _sanitize_name(self, name: str) -> str:
        """Ensures the filename ends in .db and has no illegal chars."""
        clean = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
        clean = clean.replace(' ', '_')
        if not clean.endswith('.db'):
            clean += '.db'
        return clean

# --- Independent Test Block ---
if __name__ == "__main__":
    print("Initializing Librarian Service...")
    lib = LibrarianMS("./test_brains")
    
    # 1. Create
    print("Creating 'Project_Alpha'...")
    try:
        lib.create_kb("Project Alpha")
    except FileExistsError:
        print("Project Alpha already exists.")
        
    # 2. List
    kbs = lib.list_kbs()
    print(f"Available Brains: {kbs}")
    
    # 3. Duplicate
    if "Project_Alpha.db" in kbs:
        print("Duplicating Alpha...")
        lib.duplicate_kb("Project_Alpha.db")
        
    # 4. Final List
    print(f"Final Brains: {lib.list_kbs()}")