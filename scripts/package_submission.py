"""Package the FasalSense prototype into a clean distribution ZIP file."""
from __future__ import annotations

import os
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARCHIVE_NAME = "FasalSense_Chharoli_Prototype.zip"
OUTPUT_PATH = ROOT / ARCHIVE_NAME

EXCLUDE_DIRS = {
    ".git",
    ".pytest_cache",
    ".tmp",
    ".venv",
    "venv",
    "__pycache__",
    ".agents",
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".db",
    ".sqlite",
    ".sqlite3",
}

EXCLUDE_FILES = {
    ARCHIVE_NAME,
    "fasalsense.db",
    "python.cmd",
    "uvicorn.cmd",
}


def make_archive() -> pathlib.Path:
    file_count = 0
    with zipfile.ZipFile(OUTPUT_PATH, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(ROOT):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".system_generated")]

            rel_root = pathlib.Path(root).relative_to(ROOT)

            # Skip root itself or excluded roots
            if any(part in EXCLUDE_DIRS for part in rel_root.parts):
                continue

            for file in files:
                if file in EXCLUDE_FILES or file.endswith(ARCHIVE_NAME):
                    continue
                if any(file.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                    continue

                full_path = pathlib.Path(root) / file
                rel_path = full_path.relative_to(ROOT)
                zipf.write(full_path, arcname=str(rel_path))
                file_count += 1

    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"Created archive: {OUTPUT_PATH.name} ({size_mb:.2f} MB, {file_count} files)")
    return OUTPUT_PATH


if __name__ == "__main__":
    make_archive()
