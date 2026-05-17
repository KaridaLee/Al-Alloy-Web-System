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
async def upload_file(file: UploadFile = File(...)):
    """处理文件直传：只存入目录，不再自动触发解析（改为手动统一触发）"""
    filename = file.filename
    if not filename:
        return {"success": False, "message": "无法获取文件名，上传失败"}

    if filename.endswith('.xlsx'):
        settings = load_settings()
        source_dir_str = settings.get("sourceDir", "data/source")
        source_path = Path(source_dir_str)
        dest_dir = BASE_DIR / source_path if not source_path.is_absolute() else source_path
        msg_suffix = "已存入台账待同步目录"
        
    elif filename.lower().endswith('.pdf'):
        dest_dir = BASE_DIR / "data" / "standards"
        msg_suffix = "已存入企业标准库（请点击上方按钮提取数据）"
        
    else:
        return {"success": False, "message": "仅支持上传 .xlsx 或 .pdf 格式的文件"}
    
    dest_dir.mkdir(parents=True, exist_ok=True)
    file_path = dest_dir / filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"success": True, "message": f"文件 {filename} 上传成功，{msg_suffix}"}