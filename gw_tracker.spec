# -*- mode: python -*-
# PyInstaller spec file for Guild Wars Reforge Quest Tracker

import PyInstaller
from PyInstaller.utils.hooks import collect_data_files

# --- PATHS ---
block_cipher = None
a = Analysis(['main.py'],
             pathex=['.'],
             binaries=[],
             datas=[('GW_Icon.ico', '.')],
             hiddenimports=['PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineCore', 'PySide6.QtWebChannel'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

# --- DATA FILES AND COLLECTED ASSETS ---

# Collect WebEngine data files
webengine_data = collect_data_files('PySide6', subdir='QtWebEngineWidgets')

# Bundle UI directory contents
a.datas += Tree('ui', prefix='ui')

# Add the webengine data files
a.datas += webengine_data


# --- EXE CREATION ---
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
             
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='GWReforgeTracker',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon='GW_Icon.ico')
