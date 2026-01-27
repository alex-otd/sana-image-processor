@echo off
TITLE Building Sana Image Tool

echo ========================================================
echo  Sana Commerce Image Tool Builder
echo ========================================================
echo.

:: 1. Check/Install Requirements
echo [1/3] Checking libraries (Pillow, PyInstaller)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing requirements. Check your internet connection.
    pause
    exit /b
)

:: 2. Clean previous builds (optional, keeps things tidy)
echo.
echo [2/3] Cleaning up old build files...
if exist build rmdir /s /q build
if exist *.spec del *.spec
if exist dist rmdir /s /q dist

:: 3. Build the EXE
echo.
echo [3/3] Generating Executable...
echo       (This usually takes 1-2 minutes)
echo.

:: Check if icon exists
if exist app_icon.ico (
    :: We use --add-data to bundle the icon INSIDE the exe so the script can load it for the window title
    pyinstaller --noconsole --onefile --distpath . --add-data "app_icon.ico;." --icon=app_icon.ico --name="Sana Image Tool" sana-image-processor.py
) else (
    echo WARNING: app_icon.ico not found. Building with default icon.
    pyinstaller --noconsole --onefile --distpath . --name="Sana Image Tool" sana-image-processor.py
)

if %errorlevel% neq 0 (
    echo.
    echo BUILD FAILED! Please check the errors above.
    pause
    exit /b
)

echo.
echo ========================================================
echo  SUCCESS! 
echo  Your file is located in this folder.
echo ========================================================
echo.
pause