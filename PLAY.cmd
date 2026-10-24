@echo off
setlocal
cd /d "%~dp0"
where uv >nul 2>nul
if errorlevel 1 (
    echo uv was not found. See README.md for the Python installation option.
    pause
    exit /b 1
)
uv run --no-project --python 3.12 main.py
if errorlevel 1 (
    echo.
    echo The game could not start. Please keep the error above and check README.md.
    pause
)
endlocal
