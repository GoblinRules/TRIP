# -*- mode: python ; coding: utf-8 -*-
"""
TRIP — PyInstaller spec for a single-file portable build.
"""

import os

ROOT = os.path.abspath('.')
ASSETS = os.path.join(ROOT, 'src', 'assets')
ICON = os.path.join(ROOT, 'assets', 'icon_pack', 'image3_flat_globe_magnifier.ico')

# ── Load version info resource ───────────────────────────────────────────────
_vi = {}
exec(open(os.path.join(ROOT, 'version_info.py')).read(), _vi)
VERSION_INFO = _vi['version_info']

a = Analysis(
    ['run.py'],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (ASSETS, os.path.join('src', 'assets')),
    ],
    hiddenimports=[
        'src', 'src.main', 'src.config', 'src.constants',
        'src.ip_monitor', 'src.logging_manager', 'src.notifications',
        'src.ui', 'src.ui.floating_window', 'src.ui.settings_window',
        'src.ui.tray',
        'PIL', 'PIL.Image',
        'requests', 'winotify',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy', 'pandas'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TRIP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON,
    version=VERSION_INFO,
)
