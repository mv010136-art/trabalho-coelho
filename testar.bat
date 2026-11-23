@echo off
REM Roda a suite completa de testes (leva alguns minutos)
cd /d "%~dp0"
if not exist .venv ( py -m venv .venv || python -m venv .venv )
call .venv\Scripts\activate
pip install -r requirements.txt || goto erro
python manage.py test -v 2
goto fim
:erro
echo *** Falha ao instalar dependencias. ***
:fim
pause
