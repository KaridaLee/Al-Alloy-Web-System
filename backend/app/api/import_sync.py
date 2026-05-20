import traceback
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.core.sync_engine import sync_excel_to_sqlite, sync_all_excels_in_source_dir
from app.core.config import SOURCE_DIR

router = APIRouter(prefix="/api/import", tags=["import"])

class SyncRequest(BaseModel):
    file_path: str

@router.get("/ping")
def ping():
    return {"success": True, "message": "import router ok"}

@router.post("/sync")
def sync_excel(req: SyncRequest):
    try:
        return sync_excel_to_sqlite(req.file_path)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"台账同步失败：{str(e)}")

@router.post("/sync-all")
def sync_all_excels():
    try:
        return sync_all_excels_in_source_dir()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"全量同步失败：{str(e)}")

@router.post("/external-upload")
async def external_upload_and_sync(file: UploadFile = File(...)):
    """
    专供外部程序调用的 API：上传 Excel 并立刻触发同步入库
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件名")
        
    if not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="仅支持上传 .xlsx 格式的台账文件")

    # 确保 data/source 目录存在
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    file_path = SOURCE_DIR / file.filename

    try:
        # 1. 写入文件到 data/source
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. 立刻触发针对该文件的同步解析逻辑
        sync_result = sync_excel_to_sqlite(str(file_path))
        
        return {
            "success": True,
            "message": f"文件 {file.filename} 上传并同步成功",
            "data": {
                "added": sync_result.get("added_count", 0),
                "updated": sync_result.get("updated_count", 0),
                "deleted": sync_result.get("deleted_count", 0)
            }
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"文件上传或解析失败：{str(e)}")