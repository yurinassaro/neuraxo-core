# -*- coding: utf-8 -*-
"""Cenario 7 — Seletor de empresas (sidebar) lista as empresas do usuario.

Afirma que o nome de uma empresa real do Yuri aparece no HTML do dashboard
(o seletor renderiza {{ emp.nome }} pra cada empresa de empresas_usuario).
Prova que o context_processor de empresa rodou e o vinculo Pessoa->Empresa existe.

OBS: depende de o usuario de teste ter a empresa 'Neuraxo'. Se rodar com outro
usuario, ajuste EMPRESA_ESPERADA (ou via env E2E_EMPRESA_ESPERADA).
"""
import os
from cenarios._helpers import verificar_conteudo

ID = '07'
NOME = 'Sidebar lista empresas'
CRITICO = True

EMPRESA_ESPERADA = os.getenv('E2E_EMPRESA_ESPERADA', 'Neuraxo')


def rodar(page) -> dict:
    return verificar_conteudo(
        page,
        '/',
        [EMPRESA_ESPERADA],
        f'sidebar empresa "{EMPRESA_ESPERADA}"',
    )


if __name__ == '__main__':
    from runner import _criar_browser_page
    page, ctx, browser, pw = _criar_browser_page()
    print(rodar(page))
    browser.close()
    pw.stop()
