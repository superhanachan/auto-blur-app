@echo off
cd /d "%~dp0"

echo =========================================
echo  Auto Blur ^& Track App Build Script
echo =========================================

if not exist "venv\Scripts\pyinstaller.exe" (
    echo [INFO] PyInstaller not found. Installing...
    call venv\Scripts\activate.bat
    pip install pyinstaller
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Starting build process with PyInstaller...
REM Restoring --windowed mode and adding --copy-metadata imageio
pyinstaller -y --name "AutoBlurApp" --windowed --onedir --collect-data ultralytics --collect-all imageio_ffmpeg --collect-all torchvision --copy-metadata imageio app\main.py
if errorlevel 1 goto build_error

echo [INFO] Build completed successfully.
echo [INFO] Copying models directory to dist\AutoBlurApp\models...
xcopy models dist\AutoBlurApp\models\ /E /I /Y
if errorlevel 1 goto copy_error

echo =========================================
echo [SUCCESS] Build finished!
echo [INFO] Your executable is located at:
echo %~dp0dist\AutoBlurApp\AutoBlurApp.exe
echo =========================================
pause
exit /b 0

:build_error
echo [ERROR] PyInstaller build failed.
pause
exit /b 1

:copy_error
echo [ERROR] Failed to copy models directory.
pause
exit /b 1
