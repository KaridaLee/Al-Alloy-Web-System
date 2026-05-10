import json
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import SQLITE_PATH, HOST, PORT, BASE_DIR

router = APIRouter(prefix="/api/system", tags=["system"])

SETTINGS_FILE = BASE_DIR / "data" / "system_settings.json"


class SettingsPayload(BaseModel):
    sourceDir: str = "data/source"
    syncMode: str = "manual"
    cron: str = "0 0/30 * * * *"


def load_settings():
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "sourceDir": "data/source",
        "syncMode": "manual",
        "cron": "0 0/30 * * * *"
    }


def save_settings_data(data: dict):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@router.get("/status")
def system_status():
    return {
        "host": HOST,
        "port": PORT,
        "db_path": str(SQLITE_PATH),
    }


@router.get("/settings")
def get_settings():
    return load_settings()


@router.post("/settings")
def save_settings(payload: SettingsPayload):
    data = {
        "sourceDir": payload.sourceDir,
        "syncMode": payload.syncMode,
        "cron": payload.cron
    }
    save_settings_data(data)
    return {"success": True, "settings": data}