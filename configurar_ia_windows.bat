@echo off
setlocal
cd /d "%~dp0"
set "BATALHA_PYTHON=.venv\Scripts\python.exe"
if not exist "%BATALHA_PYTHON%" set "BATALHA_PYTHON=.venv-v04\Scripts\python.exe"
if not exist "%BATALHA_PYTHON%" (
  echo Abra primeiro o iniciar_windows.bat para preparar o Python. Depois volte aqui.
  pause
  exit /b 1
)
"%BATALHA_PYTHON%" configurar_ia.py
pause
