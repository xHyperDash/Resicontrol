# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for ResiControl — onedir (folder) build."""

import sys
sys.setrecursionlimit(5000)

block_cipher = None

a = Analysis(
    ['resicontrol.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Core
        'bcrypt',
        'schedule',
        'customtkinter',
        'CTkMessagebox',
        # Pillow
        'PIL',
        'PIL._imagingtk',
        'PIL.ImageTk',
        'PIL.ImageFont',
        # QR
        'qrcode',
        'pyzbar',
        'pyzbar.pyzbar',
        'cv2',
        # Excel
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.cell',
        'et_xmlfile',
        # PDF
        'reportlab',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'reportlab.platypus',
        # Charts
        'matplotlib',
        'matplotlib.backends.backend_agg',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
        # Fonts
        'fonttools',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test',
        'unittest',
        'pytest',
        'test',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ResiControl',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ResiControl',
)