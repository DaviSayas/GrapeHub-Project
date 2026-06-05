@echo off
chcp 65001 >nul
title GrapeHub - Gestao de Garrafeira
color 0E

echo.
echo  ============================================
echo      GrapeHub - Gestao de Garrafeira
echo  ============================================
echo.

cd /d "%~dp0backend"

REM --- Create venv if missing ---
if not exist "venv\Scripts\python.exe" (
    echo  [1/3] A criar ambiente virtual Python...
    python -m venv venv
    echo       Ambiente virtual criado.
    echo.
    echo  [2/3] A instalar dependencias...
    venv\Scripts\python.exe -m pip install -q --upgrade pip
    venv\Scripts\python.exe -m pip install -q -r requirements.txt
    echo       Dependencias instaladas.
    echo.
    echo  [3/3] A inicializar base de dados...
    venv\Scripts\python.exe -m app.db.seed
    echo.
) else (
    echo  [OK] Ambiente virtual encontrado.
    echo.
)

echo  ============================================
echo   Servidor a iniciar em:
echo     http://localhost:8000
echo.
echo   Documentacao da API:
echo     http://localhost:8000/docs
echo.
echo   Conta demo:
echo     demo@grapehub.pt  /  demo123
echo  ============================================
echo.
echo  (Pressione CTRL+C para parar o servidor)
echo.

REM --- Start server (start.py forces correct working directory) ---
venv\Scripts\python.exe start.py

pause
