# <img src="https://github.com/LedyBacer/py-mkvmergre-auto/blob/main/data/icon.png" alt="Icon" width="25"/> Py MKVMerge Auto

![GUI Preview](https://github.com/LedyBacer/py-mkvmergre-auto/blob/367480ca4351f7e6b6dd2265c91e658dc99a75c7/gui_preview.png)

A simple cross-platform GUI application for automatically merging multiple MKV video files with audio tracks and subtitles. **Video, audio, and subtitles must have the same names!**

## Features

- 🎥 **Smart Merging**: Combine multiple MKV video files with matching audio/subtitle tracks. Ideal for anime and TV Series box-sets
- 🌍 **Multilingual UI**: English and Russian language support
- 🖱️ **Drag-and-Drop**: Intuitive file management. Just drag and drop folder with subtitles or audio 
- 📦 **Executable Builds**: Standalone packages for Windows and MacOS
- 🎚️ **MKVToolNix Integration**: Utilizes `mkvmerge` for merging

## Usage

Download app from [release page](https://github.com/LedyBacer/py-mkvmergre-auto/releases) and run.

## Development

### Requirements

- Conda (Miniconda/Anaconda)
- MKVToolNix (must be installed separately)
- Python 3.9+

### 1. Clone Repository
```bash
git clone https://github.com/LedyBacer/py-mkvmergre-auto.git
cd py-mkvmerge-auto
```

### 2. Create Conda Environment
```bash
conda env create -f environment.yml
conda activate py-mkvmerge-auto
```

### 3. Install MKVToolNix
- **Windows**: Download from [MKVToolNix Official Site](https://mkvtoolnix.download/)
- **Linux**:
  ```bash
  sudo apt-get install mkvtoolnix
  ```
- **macOS**:
  ```bash
  brew install mkvtoolnix
  ```

## Build Executable

1. Build package:
  - **Windows**
    ```bash
    pyinstaller ./win64.spec
    ```
  - **macOS**
    ```bash
    python setup_mac.py py2app --semi-standalone
    ```
    ```bash
    ./create_dmg.sh
    ```

2. Find executable in `dist/` directory

## 🙏 Attribution
- The application relies heavily on [MKVToolNix](https://gitlab.com/mbunkus/mkvtoolnix), so a big thanks to them.

---

*Tested on Windows 11, Macbook M4*
