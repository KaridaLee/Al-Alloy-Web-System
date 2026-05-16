import json
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File
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
    data = payload.model_dump()
    save_settings_data(data)
    return {"success": True, "message": "设置已保存"}


@router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    """
    处理台账 Excel 文件直传
    自动识别当前系统配置的源文件目录，并将文件落盘保存到该目录下
    """
    if not file.filename or not file.filename.endswith('.xlsx'):
        return {"success": False, "message": "仅支持上传后缀为 .xlsx 格式的 Excel 账表文件"}
    
    settings = load_settings()
    source_dir_str = settings.get("sourceDir", "data/source")
    source_path = Path(source_dir_str)
    
    # 兼容处理相对路径和绝对路径
    if not source_path.is_absolute():
        dest_dir = BASE_DIR / source_path
    else:
        dest_dir = source_path
        
    dest_dir.mkdir(parents=True, exist_ok=True)
    file_path = dest_dir / file.filename
    
    # 写入文件到本地
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"success": True, "message": f"文件 {file.filename} 上传成功，已存入待同步目录"}