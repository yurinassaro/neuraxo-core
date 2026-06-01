# -*- coding: utf-8 -*-
"""Cenario 1 — Smoke test login. ~3s, critico."""
import time
from playwright.sync_api import TimeoutError as PlaywrightTimeout
import config

ID = '01'
NOME = 'Smoke login'
CRITICO = True


def rodar(page) -> dict:
    inicio = time.time()
    try:
        page.goto(f"{config.BASE_URL}/login/", wait_until='domcontentloaded')
        page.fill('input[name="username"]', config.ADMIN_USER)
        page.fill('input[name="password"]', config.ADMIN_SENHA)
        page.click('button[type="submit"]')
        page.wait_for_url(lambda url: '/login' not in url, timeout=15_000)
        return {
            'sucesso': True,
            'motivo': f'logado, URL: {page.url}',
            'duracao_s': round(time.time() - inicio, 2),
        }
    except PlaywrightTimeout:
        return {
            'sucesso': False,
            'motivo': f'login nao redirecionou em 15s, URL: {page.url}',
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
