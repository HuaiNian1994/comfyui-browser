@echo off
setlocal enabledelayedexpansion

:: Read config from .devConfig
if not exist .devConfig (
    echo .devConfig not found!
    pause
    exit /b 1
)

for /f "usebackq tokens=1* delims==" %%a in (".devConfig") do (
    set "key=%%a"
    set "val=%%b"
    :: Trim spaces if necessary, but simple assignment usually works for this format
    set "!key!=!val!"
)

echo Starting ComfyUI Backend...
start "" "!COMFYUI_INSTALL_PATH!\ComfyUI.exe" --enable-cors-header

echo Starting Frontend...
cd /d "!COMFYUI_RUNTIME_PATH!\custom_nodes\comfyui-browser\web-ui"

:: Set environment variable for Vite to pick up
set "COMFYUI_SERVER_URL=!COMFYUI_SERVER_URL!"

call pnpm dev
