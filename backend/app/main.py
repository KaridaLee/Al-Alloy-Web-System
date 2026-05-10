from pathlib import Path
import sys
from typing import Optional, List

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.dashboard import router as dashboard_router
from app.api.search import router as search_router
from app.api.import_sync import router as import_router
from app.api.system import router as system_router
from app.services.sqlite_service import init_system_tables


def get_candidate_frontend_dirs() -> List[Path]:
    candidates: List[Path] = []

    # 1. 打包后 exe 同级常见位置
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / "frontend" / "dist")
        candidates.append(exe_dir / "dist")
        candidates.append(exe_dir / "_internal" / "frontend" / "dist")

    # 2. 源码目录推导
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[3]
    candidates.append(project_root / "frontend" / "dist")

    # 3. 你的本地固定路径兜底
    candidates.append(Path(r"D:\Python\Web\frontend\dist"))

    # 去重
    unique_candidates: List[Path] = []
    seen = set()
    for path in candidates:
        path_str = str(path)
        if path_str not in seen:
            seen.add(path_str)
            unique_candidates.append(path)

    return unique_candidates


def find_frontend_dist() -> Optional[Path]:
    for path in get_candidate_frontend_dirs():
        if path.exists() and path.is_dir():
            return path
    return None


app = FastAPI(title="铝锭成分台账系统")

init_system_tables()

app.include_router(dashboard_router)
app.include_router(search_router)
app.include_router(import_router)
app.include_router(system_router)

frontend_dist = find_frontend_dist()


@app.get("/api/debug/frontend-path")
def debug_frontend_path():
    return {
        "frozen": getattr(sys, "frozen", False),
        "executable": str(Path(sys.executable).resolve()) if getattr(sys, "frozen", False) else None,
        "current_file": str(Path(__file__).resolve()),
        "frontend_dist": str(frontend_dist) if frontend_dist else None,
        "candidates": [str(p) for p in get_candidate_frontend_dirs()]
    }


if frontend_dist is not None:
    assets_dir = frontend_dist / "assets"

    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def serve_index():
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {
            "message": "已找到前端目录，但缺少 index.html",
            "frontend_dist": str(frontend_dist)
        }

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        requested = frontend_dist / full_path
        if requested.exists() and requested.is_file():
            return FileResponse(requested)

        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

        return {
            "message": "前端目录存在，但 index.html 不存在",
            "frontend_dist": str(frontend_dist)
        }
else:
    @app.get("/")
    def root():
        return {
            "message": "后端运行中，但未找到前端构建文件",
            "searched_paths": [str(p) for p in get_candidate_frontend_dirs()]
        }