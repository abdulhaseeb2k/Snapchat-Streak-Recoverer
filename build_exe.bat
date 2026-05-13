@echo off
echo ===================================================
echo   Snapchat Streak Recoverer - Full Build & Setup
echo ===================================================

:: 1. Clean previous builds
echo [1/4] Cleaning old folders...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist installer_output rmdir /s /q installer_output

:: 2. Set Paths
set PY_EXE=C:\Users\Administrator\Anaconda3\envs\snapchat_recoverer\python.exe
set STEALTH_JS_SRC=C:\Users\Administrator\Anaconda3\envs\snapchat_recoverer\Lib\site-packages\playwright_stealth\js

echo Library assets path: %STEALTH_JS_SRC%

:: 3. Run PyInstaller
echo [3/4] Installing Chromium Locally ^& Running PyInstaller...
set PLAYWRIGHT_BROWSERS_PATH=0
"%PY_EXE%" -m playwright install chromium

"%PY_EXE%" -m PyInstaller --noconsole --onedir --name "app" --clean ^
  --icon "assets/APP-ICONE.ico" ^
  --add-data "%STEALTH_JS_SRC%;playwright_stealth/js" ^
  --add-data "extensions;extensions" ^
  --add-data "assets;assets" ^
  app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: PyInstaller failed.
    pause
    exit /b %ERRORLEVEL%
)

:: 4. Run Inno Setup Compiler
echo [4/4] Compiling Installer with Inno Setup...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "installer_script.iss"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Inno Setup compilation failed.
    pause
    exit /b %ERRORLEVEL%
)

:: Final Success message
echo.
echo [4/4] ALL DONE!
echo ---------------------------------------------------
echo YOUR INSTALLER: 'installer_output\Snapchat_Streak_Recoverer_Setup.exe'
echo ---------------------------------------------------
pause
