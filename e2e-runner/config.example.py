# -*- coding: utf-8 -*-
"""Configuração do E2E Runner (NeuraxoCheck).

Copie pra config.py (gitignored) e ajuste valores.
Pode usar variáveis de ambiente — recomendado pra prod.
"""
import os

# ─────────────────────────────────────────────────────────
# URL alvo
# ─────────────────────────────────────────────────────────
BASE_URL = os.getenv('E2E_BASE_URL', 'http://localhost:8007')
# Local (docker-compose): 'http://localhost:8007'
# Produção: 'http://143.110.150.237:8007'  (ou domínio quando houver)

# ─────────────────────────────────────────────────────────
# Credenciais (login = email; o backend EmailBackend aceita email no campo username)
# ─────────────────────────────────────────────────────────
# Gestor/admin de teste. Login do Neuraxo usa name="username" (aceita email).
ADMIN_USER = os.getenv('E2E_ADMIN_USER', 'yurinassarorp@gmail.com')
ADMIN_SENHA = os.getenv('E2E_ADMIN_SENHA', '@Hacker102030')

# Funcionário/executante de teste (papel não-gestor) — pra cenários de permissão.
FUNC_USER = os.getenv('E2E_FUNC_USER', 'amorimarthur133@gmail.com')
FUNC_SENHA = os.getenv('E2E_FUNC_SENHA', '@Arthur105090')

# ─────────────────────────────────────────────────────────
# Browser
# ─────────────────────────────────────────────────────────
HEADLESS = os.getenv('E2E_HEADLESS', 'true').lower() == 'true'
TIMEOUT_SEGUNDOS = 120

# ─────────────────────────────────────────────────────────
# Notificação de falha
# ─────────────────────────────────────────────────────────
NOTIFY_EMAIL_TO = os.getenv('E2E_NOTIFY_EMAIL', '')  # vazio = sem notificação
NOTIFY_ON_FAILURE_ONLY = True   # só email se falhou (não em sucesso)

SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM = os.getenv('SMTP_FROM', 'neuraxoai@gmail.com')

# ─────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────
LOG_DIR = 'logs'
RELATORIO_DIR = 'relatorios'
LOG_LEVEL = 'INFO'
