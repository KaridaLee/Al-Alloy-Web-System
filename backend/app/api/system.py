import json
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from urllib.parse import quote
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
        except Exception: pass
    return {"sourceDir": "data/source", "syncMode": "manual", "cron": "0 0/30 * * * *"}

def save_settings_data(data: dict):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

@router.get("/status")
def system_status():
    return {"host": HOST, "port": PORT, "db_path": str(SQLITE_PATH)}

@router.get("/settings")
def get_settings():
    return load_settings()

@router.post("/settings")
def save_settings(payload: SettingsPayload):
    save_settings_data(payload.model_dump())
    return {"success": True, "message": "设置已保存"}

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename
    if not filename: 
        return {"success": False, "message": "无法获取文件名，上传失败"}

    fn_lower = filename.lower()
    
    if fn_lower.endswith('.xlsx'):
        settings = load_settings()
        source_dir_str = settings.get("sourceDir", "data/source")
        source_path = Path(source_dir_str)
        dest_dir = BASE_DIR / source_path if not source_path.is_absolute() else source_path
        msg_suffix = "已存入台账待同步目录"
        
    elif fn_lower.endswith('.pdf'):
        dest_dir = BASE_DIR / "data" / "standards"
        msg_suffix = "已存入企业标准原件库"
    else:
        return {"success": False, "message": "不支持的文件类型"}

    dest_dir.mkdir(parents=True, exist_ok=True)
    file_path = dest_dir / filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"success": True, "message": f"文件 {filename} 上传成功，{msg_suffix}"}
    except Exception as e:
        return {"success": False, "message": f"文件保存失败: {str(e)}"}

# ==============================================================================
# 新增：体系文件管理模块 API
# ==============================================================================

@router.get("/docs")
def list_system_docs():
    """递归遍历 data/system 目录，拉取所有受支持的文件平铺列表"""
    docs_dir = BASE_DIR / "data" / "system"
    if not docs_dir.exists():
        docs_dir.mkdir(parents=True, exist_ok=True)
        
    allowed_exts = {".pdf", ".doc", ".docx", ".xls", ".xlsx"}
    items = []
    
    for p in docs_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in allowed_exts:
            rel_path = p.relative_to(docs_dir).as_posix()
            items.append({
                "filename": p.name,
                "rel_path": rel_path,
                "ext": p.suffix.lower()
            })
            
    # 按文件名自然排序
    items.sort(key=lambda x: x["filename"])
    return {"success": True, "items": items}

@router.get("/docs/file")
def get_system_doc_file(path: str = Query(...), download: bool = Query(False)):
    """获取指定的体系文件（支持直接预览与强制下载机制）"""
    docs_dir = BASE_DIR / "data" / "system"
    file_path = (docs_dir / path).resolve()
    
    # 路径安全拦截，防止越权遍历漏洞
    if not str(file_path).startswith(str(docs_dir.resolve())):
        return {"success": False, "message": "非法的文件路径"}
        
    if file_path.exists() and file_path.is_file():
        headers = {}
        if download:
            encoded_name = quote(file_path.name)
            headers["Content-Disposition"] = f"attachment; filename*=utf-8''{encoded_name}"
        return FileResponse(str(file_path), headers=headers)
        
    return {"success": False, "message": "请求的文件不存在或已被移除"}