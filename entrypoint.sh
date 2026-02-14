#!/bin/bash

# Rodar migrations (multi-tenant: shared + todos os schemas)
python manage.py migrate_schemas --shared --noinput
python manage.py migrate_schemas --noinput

# Criar tenant público se não existir
python manage.py create_public_tenant

# Gerar tarefas do dia (o scheduler cuida de iterar sobre os tenants)

# Iniciar scheduler em background
python manage.py scheduler >> /proc/1/fd/1 2>> /proc/1/fd/2 &

# Iniciar gunicorn
exec gunicorn --bind 0.0.0.0:8000 config.wsgi:application
