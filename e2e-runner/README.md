# E2E Runner — Playwright direto (NeuraxoCheck)

Suíte de testes E2E **determinística e rápida**. Sem LLM. Playwright dirige
o navegador com selectors fixos. ~10s pra suíte completa.

Portado do e2e-runner do Clinexo e adaptado ao stack do Neuraxo (Django,
login `/login/`, telas de checklist/demanda/aproveitamento).

## Por que sem LLM?

Pra teste de regressão de fluxo conhecido, código direto é melhor que um
agente LLM: é rápido (segundos, não minutos), determinístico e não alucina
ações. LLM é a ferramenta certa pra **exploração criativa** ("tente quebrar
o sistema"), não pra suíte de smoke — pra isso use o Playwright MCP via
Claude Code, pontualmente.

## Pré-requisitos

```bash
# Python 3.11+
cd e2e-runner
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Configuração

```bash
cp config.example.py config.py
# Edita config.py — em particular E2E_BASE_URL e as credenciais
```

`config.py` está no `.gitignore`. Pode usar env vars: `E2E_BASE_URL`,
`E2E_ADMIN_USER`, `E2E_ADMIN_SENHA`, `E2E_FUNC_USER`, `E2E_FUNC_SENHA`.

> Login do Neuraxo usa email no campo `username` (via `EmailBackend`).
> O app sobe na porta **8007** (docker-compose).

## Rodar

```bash
# Suite completa
python runner.py

# Só os críticos (todos são leitura → seguro em prod)
python runner.py --so-criticos

# IDs específicos
python runner.py --cenarios=01,05

# Com navegador visível (debug)
python runner.py --headed
```

## Cenários implementados

| ID | Nome | Crítico | Cria dados? |
|---|---|:-:|:-:|
| 01 | Smoke login | ⭐ | não |
| 02 | Dashboard carrega | ⭐ | não |
| 03 | Rotina diária carrega | ⭐ | não |
| 04 | Lista de demandas carrega | ⭐ | não |
| 05 | Aproveitamento carrega (tela do fix de IDOR) | ⭐ | não |

Todos os cenários atuais são **só leitura** → seguros em qualquer ambiente.

## Cron noturno

```bash
bash cron-example.sh
# Agenda 3h da manhã todo dia, rodando --so-criticos
```

## Notificação por email

`notify.py` envia HTML quando algo falha (SMTP configurável). Edita `config.py`:
```python
NOTIFY_EMAIL_TO = "neuraxoai@gmail.com"
SMTP_USER = "neuraxoai@gmail.com"
SMTP_PASSWORD = "..."   # senha de app do Gmail
```

## Adicionar cenário

1. Copia `cenarios/c03_rotina.py` → `cenarios/c06_meu_caso.py`
2. Ajusta `ID`, `NOME`, `CRITICO`, e a função `rodar(page)`
   (pra smoke de leitura, reusa `verificar_pagina_protegida(page, '/rota/', 'descricao')`)
3. Adiciona em `cenarios/__init__.py` na lista `TODOS_CENARIOS`

Cenário que **cria dados** (POST) deve rodar só local — marque no README e
prefira não deixá-lo `CRITICO` (pra `--so-criticos` continuar seguro em prod).

## Estrutura

```
e2e-runner/
├── README.md
├── requirements.txt          # playwright + python-dotenv
├── config.example.py         # template (config.py gitignored)
├── runner.py                 # orquestrador
├── notify.py                 # email SMTP
├── cron-example.sh           # cron diário
└── cenarios/
    ├── __init__.py           # lista TODOS_CENARIOS
    ├── _helpers.py           # fazer_login, verificar_pagina_protegida, ts
    ├── c01_login.py
    ├── c02_dashboard.py
    ├── c03_rotina.py
    ├── c04_demandas.py
    └── c05_aproveitamento.py
```
