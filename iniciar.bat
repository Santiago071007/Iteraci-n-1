@echo off
cd /d "%~dp0"
where python >nul 2>nul || (echo Instale Python 3.10 o superior desde https://www.python.org y marque "Add to PATH". & pause & exit /b 1)
if not exist .venv\Scripts\python.exe (
    echo Creando entorno virtual e instalando dependencias...
    python -m venv .venv || (pause & exit /b 1)
    .venv\Scripts\python.exe -m pip install -r requirements.txt || (pause & exit /b 1)
)
start "" http://127.0.0.1:5000
.venv\Scripts\python.exe -m flask --app app run
pause
