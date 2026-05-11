@echo off
REM build_panda3d_simple.bat - Simple Panda3D build script
REM Just double-click this file to run

echo ==============================================
echo Panda3D Build Script
echo ==============================================
echo.

REM Set up Visual Studio 2022 environment
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" x64

REM Change to project directory
cd /d "%~dp0"

REM Run the Python build script
python build_panda3d.py

if errorlevel 1 (
    echo.
    echo Build failed. Check output above.
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
pause
