# -*- mode: python ; coding: utf-8 -*-

import sys

a = Analysis(
    ['hd-verifier.py'],
    pathex=['C:\\Users\\admin\\Documents\\hd-verifier-windows\\.venv\\Lib\\site-packages'],
    binaries=[],
    datas=[('poll.py', '.'), ('main.ico', '.'), ('logo.png', '.')],
    hiddenimports=['pyrad'],  # Add pyrad as a hidden import
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
    name='helpdesk-verifier',
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
    icon=r'C:\Users\admin\Documents\hd-verifier-windows\main.ico'

)
