# -*- mode: python ; coding: utf-8 -*-
# One-file Windows executable: HermesAltUpdateGUI.exe
# Build:  pyinstaller build.spec   (needs Python 3.10+ with tkinter)

a = Analysis(
    ["hermes_update_gui.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "numpy", "scipy", "PIL", "pandas"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="HermesAltUpdateGUI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # windowed app, no console flash
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign=None,
    icon=None,
    manifest="app.manifest",   # system DPI aware: crisp UI on 2k/4k scaling
)
