@echo off
echo Building ImageUtils-crop executable...
echo.

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Run PyInstaller using the crop spec file
pyinstaller ImageUtils-crop.spec

echo.
echo Build complete! Executable is in the dist folder.
pause