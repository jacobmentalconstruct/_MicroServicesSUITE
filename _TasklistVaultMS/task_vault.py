import sqlite3
import uuid
import logging
import datetime
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Literal

# ==============================================================================
# CONFIGURATION
# ==============================================================================
DB_PATH = Path("task_vault.db")
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("TaskVault")

TaskStatus = Literal["Pending", "Running", "Complete", "Error", "Awaiting-Approval"]
# ==============================================================================

class TaskVaultMS:
    """
    The Taskmaster: A persistent SQLite engine for hierarchical task management.
    Supports infinite nesting of sub-tasks and status tracking.
    """
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            # 1. Task Lists (The containers)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_lists (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP
                )
            """)
            # 2. Tasks (The items, supporting hierarchy via parent_id)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    list_id TEXT NOT NULL,
                    parent_id TEXT,
                    content TEXT NOT NULL,
                    status TEXT DEFAULT 'Pending',
                    result TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY(list_id) REFERENCES task_lists(id) ON DELETE CASCADE,
                    FOREIGN KEY(parent_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
            """)

    # --- List Management ---

    def create_list(self, name: str) -> str:
        """Creates a new task list and returns its ID."""
        list_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO task_lists (id, name, created_at) VALUES (?, ?, ?)",
                (list_id, name, now)
            )
        log.info(f"Created Task List: '{name}' ({list_id})")
        return list_id

    def get_lists(self) -> List[Dict]:
        """Returns metadata for all task lists."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM task_lists ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    # --- Task Management ---

    def add_task(self, list_id: str, content: str, parent_id: Optional[str] = None) -> str:
        """Adds a task (or sub-task) to a list."""
        task_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO tasks (id, list_id, parent_id, content, status, created_at, updated_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (task_id, list_id, parent_id, content, "Pending", now, now)
            )
        return task_id

    def update_task(self, task_id: str, content: str = None, status: TaskStatus = None, result: str = None):
        """Updates a task's details."""
        updates = []
        params = []
        
        if content:
            updates.append("content = ?")
            params.append(content)
        if status:
            updates.append("status = ?")
            params.append(status)
        if result:
            updates.append("result = ?")
            params.append(result)
            
        if not updates: return

        updates.append("updated_at = ?")
        params.append(datetime.datetime.utcnow())
        params.append(task_id)

        sql = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        
        with self._get_conn() as conn:
            conn.execute(sql, params)
        log.info(f"Updated task {task_id}")

    # --- Tree Reconstruction ---

    def get_full_tree(self, list_id: str) -> Dict[str, Any]:
        """
        Fetches a list and reconstructs the full hierarchy of tasks.
        """
        with self._get_conn() as conn:
            # 1. Get List Info
            list_row = conn.execute("SELECT * FROM task_lists WHERE id = ?", (list_id,)).fetchone()
            if not list_row: return None
            
            # 2. Get All Tasks
            task_rows = conn.execute("SELECT * FROM tasks WHERE list_id = ?", (list_id,)).fetchall()
            
        # 3. Build Adjacency Map
        tasks_by_id = {}
        for r in task_rows:
            t = dict(r)
            t['sub_tasks'] = [] # Prepare children container
            tasks_by_id[t['id']] = t

        # 4. Link Parents and Children
        root_tasks = []
        for t_id, task in tasks_by_id.items():
            parent_id = task['parent_id']
            if parent_id and parent_id in tasks_by_id:
                tasks_by_id[parent_id]['sub_tasks'].append(task)
            else:
                root_tasks.append(task)

        return {
            "id": list_row['id'],
            "name": list_row['name'],
            "tasks": root_tasks
        }

    def delete_list(self, list_id: str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM task_lists WHERE id = ?", (list_id,))
        log.info(f"Deleted list {list_id}")

# --- Independent Test Block ---
if __name__ == "__main__":
    import os
    if DB_PATH.exists(): os.remove(DB_PATH)
    
    vault = TaskVaultMS()
    
    # 1. Create a Plan
    plan_id = vault.create_list("System Upgrade Plan")
    
    # 2. Add Root Tasks
    t1 = vault.add_task(plan_id, "Backup Database")
    t2 = vault.add_task(plan_id, "Update Server")
    
    # 3. Add Sub-Tasks
    t2_1 = vault.add_task(plan_id, "Stop Services", parent_id=t2)
    t2_2 = vault.add_task(plan_id, "Run Installer", parent_id=t2)
    
    # 4. Update Status
    vault.update_task(t1, status="Complete", result="Backup saved to /tmp/bk.tar")
    vault.update_task(t2_1, status="Running")
    
    # 5. Render Tree
    tree = vault.get_full_tree(plan_id)
    print(f"\n--- {tree['name']} ---")
    
    def print_node(node, indent=0):
        status_icon = "✓" if node['status'] == 'Complete' else "○"
        print(f"{'  '*indent}{status_icon} {node['content']} [{node['status']}]")
        for child in node['sub_tasks']:
            print_node(child, indent + 1)

    for task in tree['tasks']:
        print_node(task)
        
    # Cleanup
    if DB_PATH.exists(): os.remove(DB_PATH)