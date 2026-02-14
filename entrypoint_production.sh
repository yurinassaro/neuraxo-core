#!/bin/bash

# Rodar migrations (single-tenant)
python manage.py migrate --noinput

# Iniciar gunicorn
exec gunicorn --bind 0.0.0.0:8000 config.wsgi:application
