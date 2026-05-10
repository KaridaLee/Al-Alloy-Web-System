from pathlib import Path
import sys

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]

BASE_DIR = get_base_dir()
DATA_DIR = BASE_DIR / "data"
SOURCE_DIR = DATA_DIR / "source"
SQLITE_DIR = DATA_DIR / "sqlite"
LOG_DIR = BASE_DIR / "logs"

SQLITE_PATH = SQLITE_DIR / "app.db"

HOST = "0.0.0.0"
PORT = 9000

DATA_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)