# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for OrcaSync

import os
import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

a = Analysis(
    ['orcasync/__main__.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=[],
    hiddenimports=[
        'orcasync',
        'orcasync.cli',
        'orcasync.config',
        'orcasync.git_ops',
        'orcasync.tui',
        'click',
        'rich',
        'rich.console',
        'rich.table',
        'yaml',
        'git',
        'gitdb',
        'smmap',
        'textual',
        'textual.app',
        'textual.binding',
        'textual.containers',
        'textual.widgets',
        'textual.worker',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='orcasync',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # Set by build workflow for macOS
    codesign_identity=None,
    entitlements_file=None,
)
