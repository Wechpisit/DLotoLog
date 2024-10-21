# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['optimized_combined_loto.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/wechp/OneDrive - PTT GROUP/PTTLNG/3.Project/LNG Project/2024/2.LOTO Project/*.png', '.'), ('C:/Users/wechp/OneDrive - PTT GROUP/PTTLNG/3.Project/LNG Project/2024/2.LOTO Project/*.ico', '.'), ('config.json', '.')],
    hiddenimports=[],
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
    name='optimized_combined_loto',
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
