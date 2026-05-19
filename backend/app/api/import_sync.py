import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.sync_engine import sync_excel_to_sqlite, sync_all_excels_in_source_dir

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