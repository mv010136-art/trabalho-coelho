#!/usr/bin/env bash
# Roda a suite completa de testes (leva alguns minutos)
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py test -v 2
