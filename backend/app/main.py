from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.dashboard import router as dashboard_router
from app.api.search import router as search_router
from app.api.import_sync import router as import_router
from app.api.system import router as system_router
from app.services.sqlite_service import init_system_tables


def get_runtime_base_dir() -> Path:
    """
    运行时资源根目录：
    1. PyInstaller 打包后优先使用 _MEIPASS（真正的一体化资源目录）
    2. 否则使用源码项目根目录
    """
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent

    # 源码模式：backend/app/main.py -> project-root
    return Path(__file__).resolve().parents[3]


def get_candidate_frontend_dirs():
    base_dir = get_runtime_base_dir()
    candidates = [
        base_dir / "frontend" / "dist",
        base_dir / "dist",
    ]

    # 如果是打包运行，再附加 exe 同级目录兜底
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.extend([
            exe_dir / "frontend" / "dist",
            exe_dir / "dist",
        ])

    # 去重
    result = []
    seen = set()
    for p in candidates:
        s = str(p)
        if s not in seen:
            seen.add(s)
            result.append(p)
    return result


def find_frontend_dist():
    for path in get_candidate_frontend_dirs():
        if path.exists() and path.is_dir():
            index_file = path / "index.html"
            if index_file.exists():
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
        "meipass": getattr(sys, "_MEIPASS", None),
        "runtime_base_dir": str(get_runtime_base_dir()),
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
        return FileResponse(frontend_dist / "index.html")

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