#!/usr/bin/env bash
# Setup cron pra rodar a suite E2E todos os dias as 3h da manha.
#
# Uso:
#   1. Edita as variaveis abaixo (PROJ_DIR, VENV_PYTHON)
#   2. Roda: bash cron-example.sh
#   3. Confirma: crontab -l
#
# Logs ficam em logs/cron.log (apendado a cada execucao)

PROJ_DIR="$HOME/sistemas-python/neuraxo_check/e2e-runner"
VENV_PYTHON="$PROJ_DIR/.venv/bin/python"

# Adiciona ao crontab (linha unica, idempotente)
CRON_LINE="0 3 * * * cd $PROJ_DIR && $VENV_PYTHON runner.py --so-criticos >> logs/cron.log 2>&1"

# Remove se ja existe e adiciona de novo (evita duplicar)
( crontab -l 2>/dev/null | grep -v "$PROJ_DIR/runner.py" ; echo "$CRON_LINE" ) | crontab -

echo "Cron instalado. Rodara todo dia as 3h da manha (so cenarios criticos)."
echo
echo "Crontab atual:"
crontab -l
echo
echo "Para rodar AGORA manualmente (teste):"
echo "  cd $PROJ_DIR && $VENV_PYTHON runner.py --so-criticos"
echo
echo "Para parar de rodar via cron:"
echo "  crontab -e   # apaga a linha"
