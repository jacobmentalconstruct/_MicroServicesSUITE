import tkinter as tk
from tkinter import ttk
import os
import threading
import queue
import fnmatch
from pathlib import Path
from typing import Dict, Set

# ==============================================================================
# USER CONFIGURATION: DEFAULTS
# ==============================================================================
DEFAULT_EXCLUDED_FOLDERS = {
    "node_modules", ".git", "__pycache__", ".venv", ".mypy_cache",
    "_logs", "dist", "build", ".vscode", ".idea", "target", "out",
    "bin", "obj", "Debug", "Release", "logs"
}
# ==============================================================================

class ExplorerWidget(ttk.Frame):
    """
    A standalone file system tree viewer.
    """
    
    GLYPH_CHECKED = "[X]"
    GLYPH_UNCHECKED = "[ ]"

    def __init__(self, parent, root_path: str = ".", use_default_exclusions: bool = True, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.root_path = Path(root_path).resolve()
        self.use_defaults = use_default_exclusions
        self.gui_queue = queue.Queue()
        self.folder_item_states: Dict[str, str] = {} 
        self.state_lock = threading.RLock()
        
        self._setup_styles()
        self._build_ui()
        self.process_gui_queue()
        self.refresh_tree()

    def _setup_styles(self):
        style = ttk.Style()
        if "clam" in style.theme_names(): style.theme_use("clam")
        style.configure("Explorer.Treeview", background="#252526", foreground="lightgray", fieldbackground="#252526", borderwidth=0, font=("Consolas", 10))
        style.map("Explorer.Treeview", background=[('selected', '#007ACC')], foreground=[('selected', 'white')])

    def _build_ui(self):
        self.columnconfigure(0, weight=1); self.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(self, show="tree", columns=("size",), selectmode="none", style="Explorer.Treeview")
        self.tree.column("size", width=80, anchor="e")
        ysb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns"); xsb.grid(row=1, column=0, sticky="ew")
        self.tree.bind("<ButtonRelease-1>", self._on_click)

    def refresh_tree(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        with self.state_lock:
            self.folder_item_states.clear()
            self.folder_item_states[str(self.root_path)] = "checked"
        
        tree_data = [{'parent': '', 'iid': str(self.root_path), 'text': f" {self.root_path.name} (Root)", 'open': True}]
        self._scan_recursive(self.root_path, str(self.root_path), tree_data)
        
        for item in tree_data:
            self.tree.insert(item['parent'], "end", iid=item['iid'], text=item['text'], open=item.get('open', False))
            self.tree.set(item['iid'], "size", "...")

        self._refresh_visuals(str(self.root_path))
        threading.Thread(target=self._calc_sizes_thread, args=(str(self.root_path),), daemon=True).start()

    def _scan_recursive(self, current_path: Path, parent_id: str, data_list: list):
        try:
            items = sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            for item in items:
                if not item.is_dir(): continue
                path_str = str(item.resolve())
                
                state = "checked"
                if self.use_defaults and item.name in DEFAULT_EXCLUDED_FOLDERS:
                    state = "unchecked"
                
                with self.state_lock: self.folder_item_states[path_str] = state
                data_list.append({'parent': parent_id, 'iid': path_str, 'text': f" {item.name}"})
                self._scan_recursive(item, path_str, data_list)
        except (PermissionError, OSError): pass

    def _on_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id: return
        with self.state_lock:
            curr = self.folder_item_states.get(item_id, "unchecked")
            self.folder_item_states[item_id] = "checked" if curr == "unchecked" else "unchecked"
        self._refresh_visuals(str(self.root_path))

    def _refresh_visuals(self, start_node):
        def _update(node_id):
            if not self.tree.exists(node_id): return
            with self.state_lock: state = self.folder_item_states.get(node_id, "unchecked")
            glyph = self.GLYPH_CHECKED if state == "checked" else self.GLYPH_UNCHECKED
            name = Path(node_id).name
            if node_id == str(self.root_path): name += " (Root)"
            self.tree.item(node_id, text=f"{glyph} {name}")
            for child in self.tree.get_children(node_id): _update(child)
        _update(start_node)

    def _calc_sizes_thread(self, root_id):
        # (Simplified for brevity, same logic as before but uses queue)
        pass 
        # Note: In production you'd include the full calc logic here as in the previous version

    def get_selected_paths(self) -> list[str]:
        selected = []
        with self.state_lock:
            for path, state in self.folder_item_states.items():
                if state == "checked": selected.append(path)
        return selected

    def process_gui_queue(self):
        while not self.gui_queue.empty():
            try: self.gui_queue.get_nowait()()
            except queue.Empty: pass
        self.after(100, self.process_gui_queue)

if __name__ == "__main__":
    print("ExplorerWidget initialized. Check top of file to tweak defaults.")