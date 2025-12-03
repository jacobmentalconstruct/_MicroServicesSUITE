import os
from pathlib import Path
from typing import List, Set, Optional
import datetime

# ==============================================================================
# USER CONFIGURATION: DEFAULT EXCLUSIONS
# ==============================================================================
DEFAULT_EXCLUDES = {
    '.git', '__pycache__', '.idea', '.vscode', 'node_modules', 
    '.venv', 'env', 'venv', 'dist', 'build', '.DS_Store'
}
# ==============================================================================

class TreeMapperMS:
    """
    The Cartographer: Generates ASCII-art style directory maps.
    """
    
    def generate_tree(self, 
                      root_path: str, 
                      additional_exclusions: Optional[Set[str]] = None,
                      use_default_exclusions: bool = True) -> str:
        
        start_path = Path(root_path).resolve()
        if not start_path.exists(): return f"Error: Path '{root_path}' does not exist."

        exclusions = set()
        if use_default_exclusions:
            exclusions.update(DEFAULT_EXCLUDES)
        if additional_exclusions:
            exclusions.update(additional_exclusions)

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        lines = [
            f"Project Map: {start_path.name}",
            f"Generated: {timestamp}",
            "-" * 40,
            f"📁 {start_path.name}/"
        ]

        self._walk(start_path, "", lines, exclusions)
        return "\n".join(lines)

    def _walk(self, directory: Path, prefix: str, lines: List[str], exclusions: Set[str]):
        try:
            children = sorted(
                [p for p in directory.iterdir() if p.name not in exclusions],
                key=lambda x: (x.is_file(), x.name.lower())
            )
        except PermissionError:
            lines.append(f"{prefix}└── 🚫 [Permission Denied]")
            return

        count = len(children)
        for index, path in enumerate(children):
            is_last = (index == count - 1)
            connector = "└── " if is_last else "├── "
            
            if path.is_dir():
                lines.append(f"{prefix}{connector}📁 {path.name}/")
                extension = "    " if is_last else "│   "
                self._walk(path, prefix + extension, lines, exclusions)
            else:
                lines.append(f"{prefix}{connector}📄 {path.name}")

if __name__ == "__main__":
    print("TreeMapper initialized. Check top of file to tweak defaults.")