@echo off
cd /d "%~dp0"
py -3.12 -m pip install -r requirements.txt pyinstaller
py -3.12 -m PyInstaller --noconfirm --onefile --windowed --name Intelligent_TicTacToe --add-data "assets;assets" app.py
echo.
echo EXE created inside the dist folder.
pause
