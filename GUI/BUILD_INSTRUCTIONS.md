# Building an Executable for Animepahe Downloader GUI

## Quick Start (Windows)

### Method 1: Using the Batch Script (Easiest)

1. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Run the build script:**
   ```bash
   build_exe.bat
   ```

3. **Find your executable:**
   - The executable will be in the `dist` folder
   - File name: `Animepahe-Downloader.exe`

### Method 2: Using PyInstaller Directly

1. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Create executable (one-file, no console):**
   ```bash
   pyinstaller --onefile --windowed --name "Animepahe-Downloader" animepahe_gui.py
   ```

3. **Or use the spec file for more control:**
   ```bash
   pyinstaller animepahe_gui.spec
   ```

## Important Notes

### ⚠️ Dependencies Still Required

The executable **still needs** these files in the same directory:
- `animepahe-dl.sh` (the main download script)
- `run.sh` (optional, if you want terminal script too)

### ⚠️ System Dependencies

Users will still need these installed on their system:
- **Git Bash** (or WSL) - For running the bash script
- **jq** - JSON processor
- **Node.js** - For video link extraction
- **ffmpeg** - For video processing
- **curl** - HTTP client

The Python executable bundles PyQt5, but **not** the bash script or system tools.

## Distribution Options

### Option 1: Single Executable + Scripts Folder
```
Animepahe-Downloader.exe
animepahe-dl.sh
run.sh
README.md
```

### Option 2: Installer Package
Use tools like:
- **Inno Setup** (Windows installer creator)
- **NSIS** (Nullsoft Scriptable Install System)
- **WiX Toolset** (Microsoft installer)

These can bundle the executable + scripts + create an installer.

### Option 3: Portable Package
Create a folder with:
```
Animepahe-Downloader.exe
animepahe-dl.sh
run.sh
README.md
DEPENDENCIES.txt (instructions for users)
```

## Advanced: Bundling Everything

If you want to bundle the bash script and make it more self-contained:

1. **Modify the GUI** to include the bash script as a resource
2. **Extract it at runtime** to a temp directory
3. **Update paths** in the GUI to use the extracted script

This requires code changes to `animepahe_gui.py`.

## Troubleshooting

### "Failed to execute script"
- Make sure all dependencies are installed
- Check that `animepahe-dl.sh` is in the same folder as the executable

### "Bash not found"
- Users need Git Bash installed
- Or update the GUI to use WSL: `wsl bash animepahe-dl.sh`

### Large executable size
- PyQt5 is large (~50-100MB)
- This is normal for GUI applications
- Use `--onefile` for a single file, or `--onedir` for a folder (faster startup)

## Alternative: Create a Launcher Script

Instead of an executable, you could create a simple batch file:

**launch_gui.bat:**
```batch
@echo off
python animepahe_gui.py
pause
```

This is simpler but requires Python installed on the user's system.

