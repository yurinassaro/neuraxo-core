# -*- coding: utf-8 -*-
"""Cenario 2 — Dashboard carrega apos login. ~3s, critico, so leitura."""
import time
from playwright.sync_api import TimeoutError as PlaywrightTimeout
import config
from cenarios._helpers import fazer_login

ID = '02'
NOME = 'Dashboard carrega'
CRITICO = True


def rodar(page) -> dict:
    inicio = time.time()
    try:
        fazer_login(page)
        page.goto(f"{config.BASE_URL}/", wait_until='domcontentloaded')
        # Se voltou pro login, a sessao nao pegou
        if '/login' in page.url:
            return {
                'sucesso': False,
                'motivo': 'dashboard redirecionou pro login (sessao nao autenticada)',
                'duracao_s': round(time.time() - inicio, 2),
            }
        # body presente = pagina renderizou
        page.wait_for_selector('body', timeout=10_000)
        return {
            'sucesso': True,
            'motivo': f'dashboard OK, URL: {page.url}',
            'duracao_s': round(time.time() - inicio, 2),
        }
    except PlaywrightTimeout:
        return {
            'sucesso': False,
            'motivo': f'dashboard nao carregou em 10s, URL: {page.url}',
            'duracao_s': round(time.time() - inicio, 2),
        }
    except Exception as e:
        return {
            'sucesso': False,
            'motivo': f'{type(e).__name__}: {str(e)[:200]}',
            'duracao_s': round(time.time() - inicio, 2),
        }


if __name__ == '__main__':
    from runner import _criar_browser_page
    page, ctx, browser, pw = _criar_browser_page()
    print(rodar(page))
    browser.close()
    pw.stop()
