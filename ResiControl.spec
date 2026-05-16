# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['resicontrol.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resicontrol.db', '.'),
        ('backups', 'backups'),
        ('qrs', 'qrs'),
        ('logs', 'logs'),
    ],
    hiddenimports=[
        'bcrypt',
        'schedule',
        'PIL',
        'PIL._imagingtk',
        'PIL.ImageTk',
        'customtkinter',
        'fonttools',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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