@echo off
if not defined PORT set PORT=25495
python -m venv .venv 2>nul
call .venv\Scripts\activate.bat
pip install -r requirements.txt -q
python manage.py migrate --noinput
python manage.py runserver 0.0.0.0:%PORT%
