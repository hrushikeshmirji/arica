@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo ============================================
echo  ArecaVision AI - Local Demo Start
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on PATH.
    exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm was not found on PATH.
    exit /b 1
)

if not exist "backend\venv\Scripts\python.exe" (
    echo Creating backend virtual environment...
    python -m venv "backend\venv"
    if errorlevel 1 goto :fail
)

"backend\venv\Scripts\python.exe" -c "import fastapi, uvicorn, torch, torchvision, timm, ultralytics, cv2, bcrypt, jwt" >nul 2>&1
if errorlevel 1 (
    echo Installing backend dependencies. The first install may take several minutes...
    "backend\venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
    if errorlevel 1 goto :fail
)

if not exist "FRONTEND\node_modules" (
    echo Installing frontend dependencies...
    call npm ci --prefix FRONTEND
    if errorlevel 1 goto :fail
)

if not exist "backend\cnn\checkpoints\cnn_efficientnet_b0.pth" goto :missing_models
if not exist "backend\vit\checkpoints\vit_b16.pth" goto :missing_models
if not exist "backend\yolo\checkpoints\best.pt" goto :missing_models

powershell -NoProfile -Command "$l=Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue; if(-not $l){exit 1}; try{$h=Invoke-RestMethod 'http://127.0.0.1:8000/health' -TimeoutSec 2; if($h.status -eq 'ok'){exit 0}}catch{}; exit 2" >nul 2>&1
if errorlevel 2 (
    echo ERROR: Port 8000 is occupied by a service that failed the ArecaVision health check.
    exit /b 1
)
if errorlevel 1 (
    echo Starting backend on http://127.0.0.1:8000 ...
    start "ArecaVision Backend" /D "%ROOT%backend" "%ROOT%backend\venv\Scripts\python.exe" -m uvicorn server.app:app --host 127.0.0.1 --port 8000
) else (
    echo Reusing the healthy backend already listening on port 8000.
)

powershell -NoProfile -Command "$l=Get-NetTCPConnection -State Listen -LocalPort 8443 -ErrorAction SilentlyContinue; if(-not $l){exit 1}; try{$r=Invoke-WebRequest 'http://127.0.0.1:8443/' -UseBasicParsing -TimeoutSec 2; if($r.StatusCode -eq 200){exit 0}}catch{}; exit 2" >nul 2>&1
if errorlevel 2 (
    echo ERROR: Port 8443 is occupied by a service that did not return the Vite app.
    exit /b 1
)
if errorlevel 1 (
    echo Starting frontend on http://127.0.0.1:8443 ...
    start "ArecaVision Frontend" /D "%ROOT%FRONTEND" npm run dev -- --host 127.0.0.1
) else (
    echo Reusing the frontend already listening on port 8443.
)

echo.
echo Frontend: http://localhost:8443
echo Backend:  http://localhost:8000/health
echo Create or use a local account from the Sign In page. No shared demo password is configured.
echo Review /health: YOLO is experimental and some disease classes are not field-validated.
exit /b 0

:missing_models
echo ERROR: A required CNN, ViT, or YOLO checkpoint is missing under backend\.
exit /b 1

:fail
echo ERROR: Setup failed. Check the message above before starting the demo.
exit /b 1
