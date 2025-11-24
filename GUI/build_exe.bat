@echo off
REM Build executable for animepahe_gui.py using PyInstaller

echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building executable...
pyinstaller --onefile --windowed --name "Animepahe-Downloader" --icon=NONE animepahe_gui.py

echo.
echo Build complete! Executable is in the 'dist' folder.
echo Note: You still need animepahe-dl.sh and other dependencies in the same folder.
pause

