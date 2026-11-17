@echo off
setlocal
cd /d "%~dp0"
set "BATALHA_DADOS=%~dp0instance-feira"
set "BATALHA_PYTHON=.venv\Scripts\python.exe"
if not exist "%BATALHA_PYTHON%" set "BATALHA_PYTHON=.venv-v04\Scripts\python.exe"
if not exist "%BATALHA_PYTHON%" (
  echo Abra primeiro o iniciar_windows.bat uma vez, com internet, para preparar o Python.
  pause
  exit /b 1
)
"%BATALHA_PYTHON%" -c "import qrcode" >nul 2>&1
if errorlevel 1 (
  echo Instalando o gerador de QR code...
  "%BATALHA_PYTHON%" -m pip install -r requirements-feira.txt
)
"%BATALHA_PYTHON%" feira_qrcode.py
pause
