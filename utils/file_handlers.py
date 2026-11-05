# utils/file_handlers.py
import os
import asyncio
from pathlib import Path
from typing import Dict, List
import logging
import textwrap

logger = logging.getLogger(__name__)

IGNORE_DIRS = {
    "node_modules", ".git", ".next", "dist", "build", "out", 
    "__pycache__", "venv", ".venv", "vendor", ".idea", ".vscode"
}

IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".pdf", 
    ".exe", ".dll", ".so", ".dylib", ".zip", ".tar", ".gz",
    ".lock", ".sum", ".min.js", ".min.css", ".map"
}

MAX_FILE_SIZE_BYTES = 500 * 1024  # 500 KB limit per file

class CodebaseParser:
    def __init__(self, max_concurrent_reads: int = 100):
        self.semaphore = asyncio.Semaphore(max_concurrent_reads)

    def _is_valid_file(self, file_path: Path) -> bool:
        if file_path.suffix.lower() in IGNORE_EXTENSIONS:
            return False
        if any(part in IGNORE_DIRS for part in file_path.parts):
            return False
        try:
            if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
                logger.warning(f"Skipping {file_path.name}: Exceeds 500KB limit.")
                return False
        except OSError:
            return False
        return True

    async def _read_file_async(self, file_path: Path) -> tuple[str, str | None]:
        async with self.semaphore:
            try:
                content = await asyncio.to_thread(file_path.read_text, encoding="utf-8")
                return str(file_path), content
            except UnicodeDecodeError:
                try:
                    content = await asyncio.to_thread(file_path.read_text, encoding="latin-1")
                    return str(file_path), content
                except Exception:
                    return str(file_path), None
            except Exception:
                return str(file_path), None

    async def parse_directory(self, root_path: str | Path) -> Dict[str, str]:
        root = Path(root_path).resolve()
        if not root.exists() or not root.is_dir():
            raise NotADirectoryError(f"Invalid repository path: {root}")

        valid_files: List[Path] = []
        for dirpath, _, filenames in os.walk(root):
            for filename in filenames:
                file_path = Path(dirpath) / filename
                if self._is_valid_file(file_path):
                    valid_files.append(file_path)

        logger.info(f"Found {len(valid_files)} valid source files. Reading asynchronously...")
        tasks = [self._read_file_async(fp) for fp in valid_files]
        results = await asyncio.gather(*tasks)

        return {
            str(Path(path).relative_to(root)): content 
            for path, content in results if content is not None
        }

class CodeChunker:
    @staticmethod
    def chunk_repo_for_llm(parsed_repo: Dict[str, str], max_chars_per_chunk: int = 12000) -> List[str]:
        chunks = []
        current_chunk = ""

        for file_path, content in parsed_repo.items():
            file_text = f"\n\n### FILE: {file_path} ###\n```\n{content}\n```\n"
            
            if len(file_text) > max_chars_per_chunk:
                pieces = textwrap.wrap(file_text, width=max_chars_per_chunk, replace_whitespace=False)
                for piece in pieces:
                    chunks.append(piece)
            else:
                if len(current_chunk) + len(file_text) > max_chars_per_chunk:
                    chunks.append(current_chunk)
                    current_chunk = file_text
                else:
                    current_chunk += file_text

        if current_chunk:
            chunks.append(current_chunk)
            
        logger.info(f"Codebase chunked into {len(chunks)} contextual batches.")
        return chunks