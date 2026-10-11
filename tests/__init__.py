"""Test package initialization for FasalSense.

Configures an isolated temporary SQLite database so tests never touch
or contaminate the project's default fasalsense.db file.
"""
from __future__ import annotations

import atexit
import os
import tempfile
from pathlib import Path

# Create an isolated temporary database for test execution
_TEMP_DB = tempfile.NamedTemporaryFile(prefix="fasal_test_", suffix=".db", delete=False)
_TEMP_DB_PATH = Path(_TEMP_DB.name)
_TEMP_DB.close()

os.environ["DATABASE_URL"] = f"sqlite:///{_TEMP_DB_PATH}"


def _cleanup_test_db():
    try:
        if _TEMP_DB_PATH.exists():
            _TEMP_DB_PATH.unlink()
    except Exception:
        pass


atexit.register(_cleanup_test_db)
