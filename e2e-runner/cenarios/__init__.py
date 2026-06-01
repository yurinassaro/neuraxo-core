# -*- coding: utf-8 -*-
"""Lista canonica de cenarios E2E (Playwright direto, sem LLM).

Cada modulo cNN_*.py exporta:
  - ID: str (ex: '01')
  - NOME: str
  - CRITICO: bool (rodar mesmo em --so-criticos)
  - rodar(page) -> dict {sucesso, motivo, duracao_s}
"""
from cenarios import (
    c01_login,
    c02_dashboard,
    c03_rotina,
    c04_demandas,
    c05_aproveitamento,
    c06_demandas_conteudo,
    c07_sidebar_empresas,
)

TODOS_CENARIOS = [
    c01_login,
    c02_dashboard,
    c03_rotina,
    c04_demandas,
    c05_aproveitamento,
    c06_demandas_conteudo,     # asserção de conteúdo real
    c07_sidebar_empresas,      # asserção de conteúdo real
]
