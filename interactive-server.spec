# -*- mode: python ; coding: utf-8 -*-

from distutils.sysconfig import get_python_lib
from os import path
skimage_plugins = Tree(
    path.join(get_python_lib(), "skimage","io","_plugins"),
    prefix=path.join("skimage","io","_plugins"),
    )

skimage_files = Tree(
    path.join(get_python_lib(), "skimage"),
    prefix=path.join("skimage"),
    )


block_cipher = None


a = Analysis(['interactive-server.py'],
             pathex=[],
             binaries=[],
             datas=[('frontend/*', 'frontend')],
             hiddenimports=['websockets.legacy.server'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

# onefile
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          skimage_files,
          # exclude_binaries=True,
          name='gfp-ring-detector',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )

# # onedir
# exe = EXE(pyz,
#           a.scripts,
#           [],
#           exclude_binaries=True,
#           name='gfp-ring-detector',
#           debug=False,
#           bootloader_ignore_signals=False,
#           strip=False,
#           upx=True,
#           console=True,
#           disable_windowed_traceback=False,
#           target_arch=None,
#           codesign_identity=None,
#           entitlements_file=None )
# coll = COLLECT(exe,
#                a.binaries,
#                a.zipfiles,
#                a.datas,
#                skimage_files,
#                strip=False,
#                upx=True,
#                upx_exclude=[],
#                name='interactive-server')
