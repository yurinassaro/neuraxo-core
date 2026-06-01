# -*- coding: utf-8 -*-
"""Cenario 3 — Rotina diaria carrega. ~3s, critico, so leitura."""
from cenarios._helpers import verificar_pagina_protegida

ID = '03'
NOME = 'Rotina diaria carrega'
CRITICO = True


def rodar(page) -> dict:
    return verificar_pagina_protegida(page, '/rotina/', 'rotina diaria')


if __name__ == '__main__':
    from runner import _criar_browser_page
    page, ctx, browser, pw = _criar_browser_page()
    print(rodar(page))
    browser.close()
    pw.stop()
