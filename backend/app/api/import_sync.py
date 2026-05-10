import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.sync_engine import sync_excel_to_sqlite, sync_all_excels_in_source_dir

router = APIRouter(prefix="/api/import", tags=["import"])


class SyncRequest(BaseModel):
    file_path: str


@router.get("/ping")
def ping():
    print("[IMPORT] ping ok")
    return {"success": True, "message": "import router ok"}


@router.post("/sync")
def sync_excel(req: SyncRequest):
    print("=" * 100)
    print("[IMPORT] 收到单文件同步请求")
    print(f"[IMPORT] file_path = {req.file_path}")

    try:
        result = sync_excel_to_sqlite(req.file_path)
        print("[IMPORT] 单文件同步成功")
        print("=" * 100)
        return result
    except Exception as e:
        print("[IMPORT] 单文件同步失败，进入异常分支")
        print(f"[IMPORT] error = {repr(e)}")
        traceback.print_exc()
        print("=" * 100)
        raise HTTPException(status_code=500, detail=f"同步失败：{str(e)}")


@router.post("/sync-all")
def sync_all_excels():
    print("=" * 100)
    print("[IMPORT] 收到目录全量同步请求")

    try:
        result = sync_all_excels_in_source_dir()
        print("[IMPORT] 目录全量同步成功")
        print("=" * 100)
        return result
    except Exception as e:
        print("[IMPORT] 目录全量同步失败，进入异常分支")
        print(f"[IMPORT] error = {repr(e)}")
        traceback.print_exc()
        print("=" * 100)
        raise HTTPException(status_code=500, detail=f"目录同步失败：{str(e)}")