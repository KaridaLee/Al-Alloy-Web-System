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

# 把前端构建结果收集到发布目录里的 frontend/dist
if frontend_dist.exists():
    datas.append((str(frontend_dist), "frontend/dist"))

# 把 data 目录一起打进去
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
    [],
    exclude_binaries=True,
    name='Al_Alloy_Web',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='Al_Alloy_Web'
)