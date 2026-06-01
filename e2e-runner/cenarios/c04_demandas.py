# -*- coding: utf-8 -*-
"""Cenario 4 — Lista de demandas carrega. ~3s, critico, so leitura."""
from cenarios._helpers import verificar_pagina_protegida

ID = '04'
NOME = 'Lista de demandas carrega'
CRITICO = True


def rodar(page) -> dict:
    return verificar_pagina_protegida(page, '/demandas/', 'lista de demandas')


if __name__ == '__main__':
    from runner import _criar_browser_page
    page, ctx, browser, pw = _criar_browser_page()
    print(rodar(page))
    browser.close()
    pw.stop()
