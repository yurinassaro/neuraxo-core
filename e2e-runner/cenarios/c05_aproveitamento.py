# -*- coding: utf-8 -*-
"""Cenario 5 — Aproveitamento carrega. ~3s, critico, so leitura.

Cobre a tela que recebeu o fix de IDOR (get_pessoa_da_minha_equipe).
"""
from cenarios._helpers import verificar_pagina_protegida

ID = '05'
NOME = 'Aproveitamento carrega'
CRITICO = True


def rodar(page) -> dict:
    return verificar_pagina_protegida(page, '/aproveitamento/', 'aproveitamento')


if __name__ == '__main__':
    from runner import _criar_browser_page
    page, ctx, browser, pw = _criar_browser_page()
    print(rodar(page))
    browser.close()
    pw.stop()
