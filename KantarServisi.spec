# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(SPECPATH)
BUILD_DIR = ROOT / ".build-assets"

datas = [
    (str(ROOT / "kantar_servis" / "templates"), "kantar_servis/templates"),
    (str(ROOT / "kantar_servis" / "static"), "kantar_servis/static"),
]

a = Analysis(
    ["packaging/windows_entry.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=["pystray._win32"] if sys.platform == "win32" else [],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest"],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="KantarServisi",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(BUILD_DIR / "app.ico") if sys.platform == "win32" else None,
    version=str(BUILD_DIR / "version_info.txt") if sys.platform == "win32" else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="KantarServisi",
)
