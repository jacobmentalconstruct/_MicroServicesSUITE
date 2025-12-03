import tarfile
import os
import fnmatch
import datetime
from pathlib import Path
from typing import Set, Optional, Tuple

# ==============================================================================
# USER CONFIGURATION: DEFAULT EXCLUSIONS
# ==============================================================================
# Folders to ignore by default (Development artifacts, environments, etc.)
DEFAULT_IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    ".mypy_cache", ".pytest_cache", ".idea", ".vscode", 
    "dist", "build", "coverage", "target", "out", "bin", "obj"
}

# Files to ignore by default (System metadata, temporary files, etc.)
DEFAULT_IGNORE_FILES = {
    ".DS_Store", "Thumbs.db", "*.pyc", "*.pyo", "*.log", "*.tmp"
}
# ==============================================================================

class ArchiveBotMS:
    """
    The Archiver: Creates compressed .tar.gz backups of project folders.
    """

    def create_backup(self, 
                      source_path: str, 
                      output_dir: str, 
                      extra_exclusions: Optional[Set[str]] = None,
                      use_default_exclusions: bool = True) -> Tuple[str, int]:
        """
        Compresses the source_path into a .tar.gz file.
        
        :param use_default_exclusions: If False, ignores the DEFAULT_IGNORE lists at top of script.
        """
        src = Path(source_path).resolve()
        out = Path(output_dir).resolve()
        
        out.mkdir(parents=True, exist_ok=True)

        # Build exclusion set
        exclude_set = set()
        if use_default_exclusions:
            exclude_set.update(DEFAULT_IGNORE_DIRS)
            exclude_set.update(DEFAULT_IGNORE_FILES)
            
        if extra_exclusions:
            exclude_set.update(extra_exclusions)

        # Generate Timestamped Filename
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        archive_name = f"backup_{src.name}_{timestamp}.tar.gz"
        archive_path = out / archive_name

        file_count = 0

        try:
            with tarfile.open(archive_path, "w:gz") as tar:
                for root, dirs, files in os.walk(src):
                    # 1. Filter Directories in-place
                    for i in range(len(dirs) - 1, -1, -1):
                        d_name = dirs[i]
                        if self._is_excluded(d_name, exclude_set):
                            dirs.pop(i)
                    
                    # 2. Add Files
                    for file in files:
                        if self._is_excluded(file, exclude_set):
                            continue
                            
                        full_path = Path(root) / file
                        if full_path == archive_path: continue

                        rel_path = full_path.relative_to(src)
                        tar.add(full_path, arcname=rel_path)
                        file_count += 1
                        
            return str(archive_path), file_count

        except Exception as e:
            if archive_path.exists(): os.remove(archive_path)
            raise e

    def _is_excluded(self, name: str, patterns: Set[str]) -> bool:
        for pattern in patterns:
            if name == pattern: return True
            if fnmatch.fnmatch(name, pattern): return True
        return False

if __name__ == "__main__":
    # Test
    bot = ArchiveBotMS()
    print("ArchiveBot initialized. Check top of file to tweak defaults.")