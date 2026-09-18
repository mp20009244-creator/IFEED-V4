@echo off
setlocal
cd /d "%~dp0"
title iFeed - Django

where python >nul 2>nul
if errorlevel 1 (
  echo ERRO: Python nao foi encontrado.
  echo Instale o Python 3.10 ou superior e marque "Add Python to PATH".
  pause
  exit /b 1
)

if not exist "venv\Scripts\python.exe" (
  echo [1/5] Criando ambiente virtual...
  python -m venv venv || goto :erro
)

echo [2/5] Instalando dependencias...
"venv\Scripts\python.exe" -m pip install --upgrade pip || goto :erro
"venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :erro

echo [3/5] Preparando banco de dados...
"venv\Scripts\python.exe" manage.py migrate || goto :erro

echo [4/5] Criando dados demonstrativos...
"venv\Scripts\python.exe" manage.py seed_ifeed || goto :erro

echo [5/5] Abrindo o iFeed em http://127.0.0.1:8000/
start "" http://127.0.0.1:8000/
"venv\Scripts\python.exe" manage.py runserver
exit /b 0

:erro
echo.
echo Ocorreu um erro. Leia LEIA-ME-PRIMEIRO.md ou copie a mensagem exibida.
pause
exit /b 1
