# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.building.build_main import Analysis, EXE, PYZ  # type: ignore

# Data files to include in the build
datas = [
    ('config.json', '.'),
    ('app_config.py', '.'),
    ('functions.py', '.'),
    ('ImageUtils-logo.ico', '.'),
]

binaries = []

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'PIL',
    'PIL._tkinter_finder',
    'PIL.Image',
    'PIL.ImageTk',
]


a = Analysis(
    ['crop.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ImageUtils-crop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ImageUtils-logo.ico'
)