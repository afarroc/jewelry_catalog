@echo off
cd /d %~dp0
REM Activa el entorno virtual (ajusta la ruta si tu entorno tiene otro nombre o ubicación)
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    set PYTHON_EXE=python
) else (
    echo No se encontró el entorno virtual '.venv'. Usando Python global.
    set PYTHON_EXE=python
)

REM Inicia el servidor Django en la IP LAN (todas las interfaces) y abre la página en el navegador
start "" http://localhost:8000
%PYTHON_EXE% manage.py runserver 0.0.0.0:8000
pause
