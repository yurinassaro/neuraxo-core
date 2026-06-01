# -*- coding: utf-8 -*-
"""Orquestrador E2E — Playwright direto (sem LLM, deterministico).

Uso:
    python runner.py                       # roda tudo
    python runner.py --cenarios=01,03      # roda especificos
    python runner.py --so-criticos          # roda so os marcados CRITICO=True
    python runner.py --headed                # roda com browser visivel (debug)
"""
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime

from playwright.sync_api import sync_playwright

import config
from cenarios import TODOS_CENARIOS
from notify import notificar_resultado


def _setup_logging():
    os.makedirs(config.LOG_DIR, exist_ok=True)
    os.makedirs(config.RELATORIO_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    log_file = f"{config.LOG_DIR}/runner-{ts}.log"
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return ts


def _criar_browser_page(headed=False):
    """Cria pw + browser + ctx + page. Retorna tupla pra cleanup ordenado."""
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=not headed and config.HEADLESS,
    )
    ctx = browser.new_context(
        viewport={'width': 1280, 'height': 800},
        ignore_https_errors=True,
    )
    page = ctx.new_page()
    page.set_default_timeout(15_000)
    return page, ctx, browser, pw


def _filtrar(cenarios, ids_str=None, so_criticos=False):
    if ids_str:
        ids = [i.strip() for i in ids_str.split(',')]
        return [c for c in cenarios if c.ID in ids]
    if so_criticos:
        return [c for c in cenarios if c.CRITICO]
    return cenarios


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cenarios', help='IDs separados por virgula (ex: 01,03)')
    parser.add_argument('--so-criticos', action='store_true')
    parser.add_argument('--headed', action='store_true', help='browser visivel pra debug')
    args = parser.parse_args()

    ts = _setup_logging()
    log = logging.getLogger('runner')

    cenarios = _filtrar(TODOS_CENARIOS, args.cenarios, args.so_criticos)
    log.info("=" * 70)
    log.info("Suite E2E NeuraxoCheck - %d cenarios - URL: %s", len(cenarios), config.BASE_URL)
    log.info("=" * 70)

    inicio_total = time.time()
    resultados = []

    page, ctx, browser, pw = _criar_browser_page(headed=args.headed)
    try:
        for c in cenarios:
            log.info(">>> %s - %s", c.ID, c.NOME)
            try:
                r = c.rodar(page)
            except Exception as e:
                log.exception("Crash em %s", c.ID)
                r = {'sucesso': False, 'motivo': f'crash: {e}', 'duracao_s': 0}
            r['id'] = c.ID
            r['nome'] = c.NOME
            emoji = '✓' if r['sucesso'] else '✗'
            log.info("    %s %s (%.2fs) - %s", emoji, c.NOME,
                     r.get('duracao_s', 0), r.get('motivo', '')[:160])
            resultados.append(r)
            # Reset de contexto entre cenarios (limpa cookies/storage)
            ctx.clear_cookies()
    finally:
        browser.close()
        pw.stop()

    sucessos = sum(1 for r in resultados if r['sucesso'])
    falhas = len(resultados) - sucessos
    duracao_total = round(time.time() - inicio_total, 2)

    log.info("=" * 70)
    log.info("Total %d / OK %d / Falhas %d / Duracao %ss",
             len(resultados), sucessos, falhas, duracao_total)
    log.info("=" * 70)

    relatorio = {
        'data': ts,
        'base_url': config.BASE_URL,
        'total': len(resultados),
        'sucessos': sucessos,
        'falhas': falhas,
        'duracao_total_s': duracao_total,
        'cenarios': resultados,
    }
    rel_path = f"{config.RELATORIO_DIR}/relatorio-{ts}.json"
    with open(rel_path, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    log.info("Relatorio: %s", rel_path)

    if config.NOTIFY_EMAIL_TO:
        notificar_resultado(relatorio)

    sys.exit(0 if falhas == 0 else 1)


if __name__ == '__main__':
    main()
