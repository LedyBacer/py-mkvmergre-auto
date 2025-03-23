# Py Mkvmerge Auto

![GUI Preview](https://github.com/LedyBacer/py-mkvmergre-auto/blob/main-qt/gui_preview.png)

A cross-platform GUI application for automatically merging video files with audio tracks and subtitles using MKVToolNix. Supports drag-and-drop, multilingual interface (English/Russian), and executable packaging.

## Features

- 🎥 **Smart Merging**: Combine video files with matching audio/subtitle tracks
- 🌍 **Multilingual UI**: English and Russian language support
- 🖱️ **Drag-and-Drop**: Intuitive file management
- 📦 **Executable Builds**: Standalone packages for each system
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
   ```bash
   pyinstaller ./win64.spec
   ```

2. Find executable in `dist/` directory

## 🙏Attribution
- The application relies heavily on [MKVToolNix](https://gitlab.com/mbunkus/mkvtoolnix), so a big thanks to them.

---

*Tested on Windows 11*
