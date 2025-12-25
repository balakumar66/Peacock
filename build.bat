@echo off
REM Build script for creating Peacock executable on Windows

echo Building Peacock Executable...
echo ==================================

REM Check if pyinstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

REM Build executable
echo Building executable...
pyinstaller --onefile --name Peacock peacock.py

REM Create distribution package
echo Creating distribution package...
if not exist Peacock-Distribution mkdir Peacock-Distribution
copy dist\Peacock.exe Peacock-Distribution\
copy config.example.json Peacock-Distribution\
copy README.md Peacock-Distribution\
copy LICENSE Peacock-Distribution\

echo.
echo Build complete!
echo Executable: dist\Peacock.exe
echo Distribution package: Peacock-Distribution\
echo.
echo To create a ZIP for sharing, use Windows Explorer or:
echo   powershell Compress-Archive -Path Peacock-Distribution -DestinationPath Peacock.zip
pause
