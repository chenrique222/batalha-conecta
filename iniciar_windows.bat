@echo off
setlocal
cd /d "%~dp0"
echo BATALHA CONECTA - versao 0.7 - assistente de IA para ouvir e entender
echo.
set "BATALHA_AMBIENTE=.venv"
set "BATALHA_PYTHON=.venv\Scripts\python.exe"
if exist "%BATALHA_PYTHON%" (
  "%BATALHA_PYTHON%" -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
  if not errorlevel 1 goto instalar
  set "BATALHA_AMBIENTE=.venv-v04"
  set "BATALHA_PYTHON=.venv-v04\Scripts\python.exe"
)
if exist "%BATALHA_PYTHON%" goto instalar
rem Python 3.12 e recomendado; um Python compativel ja instalado tambem serve.
py -3.12 -m venv "%BATALHA_AMBIENTE%" >nul 2>&1
if not errorlevel 1 goto instalar
py -3 -m venv "%BATALHA_AMBIENTE%" >nul 2>&1
if not errorlevel 1 goto instalar
python -m venv "%BATALHA_AMBIENTE%"
if errorlevel 1 goto erro_python

:instalar
"%BATALHA_PYTHON%" -c "import sys; print('Python selecionado:', sys.version.split()[0]); sys.exit(sys.version_info < (3, 10))"
if errorlevel 1 goto erro_python
"%BATALHA_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Falha nas dependencias basicas. Veja a mensagem do pip acima.
  pause
  exit /b 1
)
echo.
echo Instalando a nova narracao. Nao usa Piper nem ONNX Runtime.
"%BATALHA_PYTHON%" -m pip install -r requirements-voz.txt
if errorlevel 1 (
  echo A voz natural nao foi instalada. O app usara a voz do aparelho.
)
echo.
echo Abra no navegador: http://127.0.0.1:5000
echo Em Ajuda, escolha e ouca Francisca ou Antonio. As vozes usam internet.
if exist ".env" (echo Assistente de IA: arquivo .env encontrado.) else (echo Assistente de IA desativado. Para ativar gratis, abra configurar_ia_windows.bat.)
echo Mantenha esta janela aberta. Para encerrar, pressione Ctrl+C.
"%BATALHA_PYTHON%" app.py
pause
exit /b

:erro_python
echo Nao foi possivel preparar o Python. Recomendamos Python 3.12 de 64 bits.
echo Se o comando py estiver disponivel, execute: py install 3.12
echo https://www.python.org/downloads/windows/
pause
exit /b 1
