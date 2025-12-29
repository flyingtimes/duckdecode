# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller配置文件 - Duck Decode GUI
用于将Python程序打包为独立的Windows可执行文件
"""

block_cipher = None

a = Analysis(
    ['duck_decode_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt5',
        'numpy',
        'PIL',
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
    name='DuckDecode',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加 .ico 图标文件路径
    version_file=None,
)