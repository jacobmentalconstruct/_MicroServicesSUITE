import os
from typing import List, Dict, Any, Optional
from pathlib import Path

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# Map extensions to tree-sitter language names
LANG_MAP = {
    ".py": "python",
    ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".cpp": "cpp", ".cc": "cpp", ".c": "c", ".h": "c"
}

# The "Atomic Units" we want to keep whole
CHUNK_NODES = {
    "class_definition", "function_definition", "method_definition", # Python
    "class_declaration", "function_declaration", "method_definition", # JS/TS
    "func_literal", "function_declaration", # Go
    "function_item", "impl_item" # Rust
}

class CodeChunkerMS:
    """
    The Surgeon: Uses Tree-Sitter (CST) to structurally parse code.
    Splits files into 'Semantic Chunks' (Classes, Functions) rather than
    arbitrary text slices. Preserves comments and docstrings.
    """
    def __init__(self):
        self._available = False
        try:
            from tree_sitter import Parser
            from tree_sitter_languages import get_language
            self.Parser = Parser
            self.get_language = get_language
            self._available = True
        except ImportError:
            print("CRITICAL: tree-sitter not installed. Chunker will fail.")

    def chunk_file(self, file_path: str, max_chars: int = 1500) -> List[Dict[str, Any]]:
        """
        Reads a file and breaks it into semantic code blocks.
        """
        if not self._available: return []
        
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext not in LANG_MAP:
            return [] # fallback to text chunker for unknown types?

        lang_id = LANG_MAP[ext]
        try:
            code = path.read_text(encoding="utf-8", errors="ignore")
            return self._parse(code, lang_id, max_chars)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []

    def _parse(self, code: str, lang_id: str, max_chars: int) -> List[Dict]:
        language = self.get_language(lang_id)
        parser = self.Parser()
        parser.set_language(language)
        
        tree = parser.parse(bytes(code, "utf8"))
        chunks = []
        
        # Cursor allows efficient traversal
        cursor = tree.walk()
        
        # Recursive walker to find significant nodes
        def walk(node):
            # If this node is a major block (Function/Class)
            if node.type in CHUNK_NODES:
                # 1. Capture the code including preceding comments
                start_byte = node.start_byte
                end_byte = node.end_byte
                
                # Look backwards for docstrings/comments attached to this node
                # (Simple heuristic: scan previous sibling)
                prev = node.prev_sibling
                if prev and prev.type == "comment":
                    start_byte = prev.start_byte

                chunk_text = code[start_byte:end_byte]
                
                # 2. Check size
                if len(chunk_text) > max_chars:
                    # Too big? Recurse into children (split the function apart)
                    for child in node.children:
                        walk(child)
                else:
                    # Good size? Keep it as a chunk
                    chunks.append({
                        "type": node.type,
                        "text": chunk_text,
                        "start_line": node.start_point[0],
                        "end_line": node.end_point[0]
                    })
                return # Don't recurse if we kept the parent

            # If not a major node, just keep walking down
            for child in node.children:
                walk(child)

        walk(tree.root_node)
        
        # Fallback: If no structural chunks found (e.g. flat script), return whole file
        if not chunks and code.strip():
            chunks.append({
                "type": "file", 
                "text": code, 
                "start_line": 0, 
                "end_line": len(code.splitlines())
            })
            
        return chunks

# --- Independent Test Block ---
if __name__ == "__main__":
    # Test with a dummy Python file
    chunker = CodeChunkerMS()
    
    if chunker._available:
        py_code = """
        # This is a helper function
        def helper(x):
            return x * 2

        class Processor:
            '''
            Main processing class.
            '''
            def process(self, data):
                # Process the data
                if data:
                    return helper(data)
                return None
        """
        
        # Write temp file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as tmp:
            tmp.write(py_code)
            tmp_path = tmp.name
            
        print(f"--- Chunking {tmp_path} ---")
        chunks = chunker.chunk_file(tmp_path)
        
        for i, c in enumerate(chunks):
            print(f"\n[Chunk {i}] Type: {c['type']} (Lines {c['start_line']}-{c['end_line']})")
            print(f"{'-'*20}\n{c['text'].strip()}\n{'-'*20}")
            
        os.remove(tmp_path)
    else:
        print("Skipping test: tree-sitter not installed.")