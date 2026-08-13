"""
Test setup.

This small file lets the tests import the application (``from app.main import
app``) no matter which folder you run pytest from. It adds the "backend"
folder to Python's import path.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
