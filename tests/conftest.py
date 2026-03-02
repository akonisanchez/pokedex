import sys
from pathlib import Path

# Ensures the project root is on the Python path so tests can import app.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))