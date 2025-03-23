# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('binary/macos/mkvmerge', 'mkvtoolnix'),
        ('binary/macos/mkvmerge', '.'),
        ('data/icon.png', 'icons')
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtMacExtras',
        'PyQt6.QtDBus'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='Py Mkvmerge Auto',
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='data/icon.icns'  # Укажите путь к иконке
)

app = BUNDLE(
    exe,
    name='Py Mkvmerge Auto.app',
    icon='data/icon.icns',
    bundle_identifier='com.bacer.py_mkvmerge_auto',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.15',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0'
    },
)