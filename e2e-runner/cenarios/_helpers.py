# -*- coding: utf-8 -*-
"""Helpers comuns aos cenarios."""
import time

import config


def fazer_login(page, usuario=None, senha=None) -> None:
    """Login reutilizado nos cenarios. Default = admin (gestor).

    Login do Neuraxo: Django auth_views.LoginView em /login/, com
    name="username" (aceita email via EmailBackend) e name="password".
    Sucesso = redireciona pra fora de /login.
    """
    usuario = usuario or config.ADMIN_USER
    senha = senha or config.ADMIN_SENHA
    page.goto(f"{config.BASE_URL}/login/", wait_until='domcontentloaded')
    page.fill('input[name="username"]', usuario)
    page.fill('input[name="password"]', senha)
    page.click('button[type="submit"]')
    page.wait_for_url(lambda url: '/login' not in url, timeout=15_000)


def ts() -> str:
    """Timestamp pra nome unico em cadastros de teste."""
    return time.strftime('%Y%m%d%H%M%S')


def verificar_pagina_protegida(page, caminho, descricao, usuario=None, senha=None) -> dict:
    """Smoke de leitura: loga, abre `caminho` e confirma que renderizou sem
    cair de volta no /login. Seguro em prod (so GET). Retorna o dict padrao.

    caminho: path relativo (ex: '/rotina/'). descricao: texto pro motivo.
    """
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    inicio = time.time()
    try:
        fazer_login(page, usuario, senha)
        page.goto(f"{config.BASE_URL}{caminho}", wait_until='domcontentloaded')
        if '/login' in page.url:
            return {
                'sucesso': False,
                'motivo': f'{descricao} redirecionou pro login (sem permissao/sessao)',
                'duracao_s': round(time.time() - inicio, 2),
            }
        page.wait_for_selector('body', timeout=10_000)
        return {
            'sucesso': True,
            'motivo': f'{descricao} OK, URL: {page.url}',
            'duracao_s': round(time.time() - inicio, 2),
        }
    except PlaywrightTimeout:
        return {
            'sucesso': False,
            'motivo': f'{descricao} nao carregou em 10s, URL: {page.url}',
            'duracao_s': round(time.time() - inicio, 2),
        }
    except Exception as e:
        return {
            'sucesso': False,
            'motivo': f'{type(e).__name__}: {str(e)[:200]}',
            'duracao_s': round(time.time() - inicio, 2),
        }


def verificar_conteudo(page, caminho, esperados, descricao, usuario=None, senha=None) -> dict:
    """Smoke de conteudo (leitura): loga, abre `caminho` e confirma que TODOS os
    textos em `esperados` (lista de str) estao presentes no HTML renderizado.
    Diferente de verificar_pagina_protegida, aqui afirmamos o que a tela mostra.

    Seguro em prod (so GET). Retorna o dict padrao.
    """
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    inicio = time.time()
    try:
        fazer_login(page, usuario, senha)
        page.goto(f"{config.BASE_URL}{caminho}", wait_until='domcontentloaded')
        if '/login' in page.url:
            return {
                'sucesso': False,
                'motivo': f'{descricao} redirecionou pro login (sem permissao/sessao)',
                'duracao_s': round(time.time() - inicio, 2),
            }
        page.wait_for_selector('body', timeout=10_000)
        html = page.content()
        faltando = [t for t in esperados if t not in html]
        if faltando:
            return {
                'sucesso': False,
                'motivo': f'{descricao}: nao encontrei no HTML: {faltando}',
                'duracao_s': round(time.time() - inicio, 2),
            }
        return {
            'sucesso': True,
            'motivo': f'{descricao} OK, conteudo presente: {esperados}',
            'duracao_s': round(time.time() - inicio, 2),
        }
    except PlaywrightTimeout:
        return {
            'sucesso': False,
            'motivo': f'{descricao} nao carregou em 10s, URL: {page.url}',
            'duracao_s': round(time.time() - inicio, 2),
        }
    except Exception as e:
        return {
            'sucesso': False,
            'motivo': f'{type(e).__name__}: {str(e)[:200]}',
            'duracao_s': round(time.time() - inicio, 2),
        }
