#!/usr/bin/env bash
# Prepara tudo e abre o site em http://127.0.0.1:8000/  (so para teste local)
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_EMAIL=admin@example.com DJANGO_SUPERUSER_PASSWORD=admin12345 \
  python manage.py createsuperuser --noinput 2>/dev/null || true
python manage.py seed_demo --demo-customer
python manage.py check
python manage.py makemigrations --check --dry-run
echo "===== Site: http://127.0.0.1:8000/ ====="
echo "Equipe: admin / admin12345   Cliente: cliente_demo / demo12345"
python manage.py runserver
