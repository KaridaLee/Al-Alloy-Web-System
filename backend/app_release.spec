# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

backend_dir = Path.cwd()               # backend/
project_root = backend_dir.parent      # project-root/
frontend_dist = project_root / "frontend" / "dist"
data_dir = project_root / "data"

hiddenimports = []
hiddenimports += collect_submodules("uvicorn")
hiddenimports += collect_submodules("fastapi")
hiddenimports += collect_submodules("sqlalchemy")
hiddenimports += collect_submodules("openpyxl")

datas = []

# 把前端构建产物打进去，运行时从 _MEIPASS/frontend/dist 读取
if frontend_dist.exists():
    datas.append((str(frontend_dist), "frontend/dist"))

# data 目录如果存在，也打进去
if data_dir.exists():
    datas.append((str(data_dir), "data"))

a = Analysis(
    ['run.py'],
    pathex=[str(backend_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Al_Alloy_Web',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)