# Spec: Log de acesso a item do cofre de senhas (auditoria)

> Status: `draft`
> Spec #: 001 · Autor: exemplo · Data: 2026-06-01

> ⚠️ Este é um EXEMPLO preenchido para a skill `spec`, no stack Django do
> NeuraxoCheck. Baseado num gap plausível: hoje o cofre criptografa os segredos
> com Fernet, mas não registra QUEM visualizou/descriptografou cada item — útil
> para auditoria de acesso a credenciais compartilhadas entre a equipe.

## 1. Por quê (motivação)

O cofre guarda senhas compartilhadas por empresa (criptografadas com Fernet). Hoje
qualquer pessoa com acesso ao cofre da empresa pode revelar um segredo, mas não há
rastro de quem viu o quê. Para credenciais sensíveis (banco, ERP), o gestor precisa
saber quem acessou e quando — sem esse log, um vazamento é impossível de investigar.

## 2. O quê (escopo)

**Dentro do escopo:**
- Registrar um log `CofreAcesso(item, pessoa, data_hora)` toda vez que um item do cofre é revelado/descriptografado.
- Tela simples (só gestor) listando os acessos de um item.

**Fora do escopo (explícito):**
- Alertas/notificação em tempo real de acesso — outra spec.
- Expurgo/retenção de logs antigos.

## 3. Regra de negócio

- Toda revelação de segredo do cofre gera 1 registro de acesso.
- O log registra: pessoa, item do cofre, empresa, data/hora.
- Só gestor da empresa do item pode ver a lista de acessos daquele item.
- Falha ao gravar o log NÃO bloqueia a revelação do segredo (best-effort, loga se falhar).

## 4. Contrato (rotas/views)

| Método | URL (nome) | Entrada | Saída | Status | Acesso (papel) |
|--------|-----------|---------|-------|--------|----------------|
| POST | cofre:revelar_item | item_id (path), senha-mestre | JSON {segredo} | 200/403/404 | @login_required + tem acesso ao cofre da empresa |
| GET | cofre:acessos_item | item_id (path) | render lista | 200/403/404 | @login_required + gestor da empresa do item |

## 5. Plano de camadas

**View (`financeiro/views.py` ou app do cofre) — FINA:**
- `revelar_item(request, item_id)`: carrega item escopado por empresa do usuário (404 se for de outra empresa), descriptografa via serviço Fernet, chama `registrar_acesso_cofre(item, pessoa)` dentro de try/except best-effort, retorna JSON.
- `acessos_item(request, item_id)`: valida `pessoa.is_gestor_empresa(item.empresa)`, lista `CofreAcesso` do item.

**Model / serviço:**
- `CofreAcesso(models.Model)`: FKs `item`, `pessoa`, `empresa`; `data_hora = auto_now_add`.
- `registrar_acesso_cofre(item, pessoa)`: cria o registro (função de serviço, testável sem HTTP).
- Reusa o serviço Fernet existente de criptografia do cofre.

**ORM / QuerySets:**
- `CofreItem.objects.filter(empresa__in=empresas_do_usuario, pk=item_id)` — escopo + IDOR safe.
- `CofreAcesso.objects.filter(item=item).order_by('-data_hora')`.

**Banco (migration):**
- Novo model `CofreAcesso` → `makemigrations` gera a migration.

## 6. Multi-tenant (isolamento por Empresa)

- O item do cofre é carregado com `empresa__in=get_empresas_filtradas(pessoa, request)` — usuário de outra empresa recebe 404, nunca o segredo.
- A lista de acessos exige `is_gestor_empresa(item.empresa)`.
- super_admin/staff: mesma regra (auditoria é o dado mais sensível — sem isenção).

## 7. Critérios de aceite

- [ ] **DADO** uma pessoa com acesso ao cofre da empresa A **QUANDO** revela o item 10 (da empresa A) **ENTÃO** é criado 1 `CofreAcesso(item=10, pessoa=ela)`
- [ ] **DADO** uma pessoa da empresa B **QUANDO** tenta revelar o item 10 (empresa A) **ENTÃO** recebe 404 e nenhum segredo é retornado
- [ ] **DADO** um colaborador (não gestor) **QUANDO** abre a lista de acessos do item **ENTÃO** recebe 403
- [ ] **DADO** que a gravação do log falhe **QUANDO** a pessoa revela o item **ENTÃO** o segredo ainda é retornado (log não bloqueia)

## 8. Testes (Django TestCase)

- `tests.py::test_revelar_gera_log_acesso` — assert `CofreAcesso` criado com pessoa/item corretos
- `tests.py::test_outra_empresa_nao_revela` — usuário empresa B → 404 no item da empresa A
- `tests.py::test_lista_acessos_so_gestor` — colaborador → 403
- `tests.py::test_falha_log_nao_bloqueia` — mock `registrar_acesso_cofre` lança exceção, revelação ainda retorna 200

## 9. Riscos / decisões abertas

- Volume: cada revelação gera 1 row. Avaliar índice em `(item, data_hora)` se crescer.
- Decisão: registrar também tentativas de acesso negadas (empresa errada)? (provável sim, fase 2)
