# -*- coding: utf-8 -*-
"""Cenario 6 — Lista de demandas mostra conteudo real. ~1s, critico, so leitura.

Diferente do c04 (so 'abriu'), aqui afirmamos que a tela renderiza o cabecalho
'Pendencias' e o contador de pendentes — prova que o agrupamento por empresa
rodou e a query trouxe dados, nao so um 200 vazio.
"""
from cenarios._helpers import verificar_conteudo

ID = '06'
NOME = 'Demandas mostra conteudo'
CRITICO = True


def rodar(page) -> dict:
    return verificar_conteudo(
        page,
        '/demandas/',
        ['Pendencias', 'pendente(s)'],
        'demandas conteudo',
    )


if __name__ == '__main__':
    from runner import _criar_browser_page
    page, ctx, browser, pw = _criar_browser_page()
    print(rodar(page))
    browser.close()
    pw.stop()
