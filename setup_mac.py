from setuptools import setup
import os
import glob

def get_data_files():
    data_files = []
    
    # Иконка
    data_files.append(('data', ['data/icon.png']))
    
    # Mkvmerge и библиотеки
    macos_bin = 'binary/macos'
    libs_dir = os.path.join(macos_bin, 'libs')
    
    # Исполняемый файл
    data_files.append((macos_bin, [os.path.join(macos_bin, 'mkvmerge')]))
    
    # Библиотеки
    libs = glob.glob(os.path.join(libs_dir, '*.dylib'))
    data_files.append((libs_dir, libs))
    
    return data_files

APP = ['main.py']
DATA_FILES = [
    ('data', ['data/icon.png']),
    ('binary/macos', ['binary/macos/mkvmerge'])  # Путь может отличаться
]
OPTIONS = {
    'argv_emulation': True,
    'arch': 'arm64',
    'plist': {
        'CFBundleName': 'Py MKVMerge Auto',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleIconFile': 'data/icon.png',
        'NSHumanReadableCopyright': 'Copyright © 2025 Bacer',
        'LSEnvironment': {
            'DYLD_LIBRARY_PATH': '@executable_path/../Resources/binary/macos/libs'
        }
    },
    'packages': ['PyQt6', 'process_data'],
}

setup(
    app=APP,
    data_files=get_data_files(),
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)