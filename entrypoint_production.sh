#!/bin/bash

# Rodar migrations
python manage.py migrate --noinput

# Iniciar scheduler em background
python manage.py scheduler >> /proc/1/fd/1 2>> /proc/1/fd/2 &

# Iniciar gunicorn
exec gunicorn --bind 0.0.0.0:8000 config.wsgi:application
