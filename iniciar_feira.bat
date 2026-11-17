@echo off
setlocal
cd /d "%~dp0"
echo BATALHA CONECTA - MODO FEIRA
echo.
rem Os cadastros de teste ficam na pasta instance-feira, separados dos cadastros de verdade (pasta instance).
set "BATALHA_DADOS=%~dp0instance-feira"
set "BATALHA_PYTHON=.venv\Scripts\python.exe"
if not exist "%BATALHA_PYTHON%" set "BATALHA_PYTHON=.venv-v04\Scripts\python.exe"
if not exist "%BATALHA_PYTHON%" (
  echo Abra primeiro o iniciar_windows.bat uma vez, com internet, para preparar o Python.
  pause
  exit /b 1
)
if exist ".env" (echo Assistente de IA: ativo.) else (echo ATENCAO: sem o arquivo .env o assistente de IA fica desligado.)
echo Os testes da feira ficam em: %BATALHA_DADOS%
echo Ao final da feira, feche esta janela e apague a pasta instance-feira.
echo.
echo Abra no navegador: http://127.0.0.1:5000
echo Mantenha esta janela aberta. Para encerrar, pressione Ctrl+C.
"%BATALHA_PYTHON%" servir.py
pause
