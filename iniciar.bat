@echo off
REM Prepara tudo e abre o site em http://127.0.0.1:8000/  (so para teste local)
cd /d "%~dp0"
if not exist .venv ( py -m venv .venv || python -m venv .venv )
call .venv\Scripts\activate
pip install -r requirements.txt || goto erro
python manage.py migrate || goto erro
set DJANGO_SUPERUSER_USERNAME=admin
set DJANGO_SUPERUSER_EMAIL=admin@example.com
set DJANGO_SUPERUSER_PASSWORD=admin12345
python manage.py createsuperuser --noinput 2>nul
python manage.py seed_demo --demo-customer || goto erro
python manage.py check || goto erro
python manage.py makemigrations --check --dry-run || goto erro
echo.
echo ===== Site: http://127.0.0.1:8000/ =====
echo Equipe: admin / admin12345   Cliente: cliente_demo / demo12345
python manage.py runserver
goto fim
:erro
echo.
echo *** Deu erro acima. Copie a mensagem e mande para o Claude. ***
:fim
pause
