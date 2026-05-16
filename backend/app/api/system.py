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
    """
    处理文件直传：自动判断文件类型
    .xlsx -> 存入台账目录
    .pdf  -> 存入企业标准目录，并触发 PDF 解析存入独立 DB
    """
    # 提取文件名并处理 None 的情况，消除类型检查警告
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
        msg_suffix = "已存入企业标准库并开始解析"
        
    else:
        return {"success": False, "message": "仅支持上传 .xlsx 或 .pdf 格式的文件"}
    
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # 此时 filename 已经被保证是 str 类型，拼接不会再报错
    file_path = dest_dir / filename
    
    # 写入文件到本地
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 如果是 PDF，触发企业标准解析引擎
    if filename.lower().endswith('.pdf'):
        try:
            from app.core.standard_engine import sync_pdf_standard
            sync_pdf_standard(str(file_path))
            return {"success": True, "message": f"标准文件 {filename} 上传并解析入库成功！"}
        except Exception as e:
            return {"success": False, "message": f"PDF 上传成功，但提取标准数据失败: {str(e)}"}
        
    return {"success": True, "message": f"文件 {filename} 上传成功，{msg_suffix}"}