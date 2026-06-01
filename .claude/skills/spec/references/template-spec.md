# Spec: <Nome da Feature>

> Status: `draft` | `aprovada` | `em-implementacao` | `done`
> Spec #: NNN · Autor: <quem> · Data: AAAA-MM-DD

## 1. Por quê (motivação)

<O problema que isso resolve. 2-4 linhas. Por que agora?>

## 2. O quê (escopo)

**Dentro do escopo:**
- <item>

**Fora do escopo (explícito):**
- <o que NÃO vamos fazer agora — evita scope creep>

## 3. Regra de negócio

<Bullets curtos e VERIFICÁVEIS. Cada regra que vai pra produção tem 1 bullet.>
- <regra 1>
- <regra 2>

## 4. Contrato (rotas/views)

| Método | URL (nome) | Entrada | Saída | Status | Acesso (papel) |
|--------|-----------|---------|-------|--------|----------------|
| GET/POST | app:nome_da_url | form/json campos | render/json | 200/302/400/403 | @login_required + gestor/colaborador/executante |

<Detalhe campos de entrada e formato de saída se não couber na tabela.>

## 5. Plano de camadas  ⬅️ coração do método

**View (`<app>/views.py`) — FINA, só orquestra:**
- view X: valida auth/papel → carrega contexto escopado por empresa → chama `model/serviço` → render/redirect

**Model / serviço (`<app>/models.py` ou `services.py`) — lógica:**
- `metodo(...)`: <o que faz, qual regra aplica, qual QuerySet roda>

**ORM / QuerySets:**
- <QuerySets de leitura/escrita, sempre `.filter(empresa__in=...)`>

**Banco (migration, se houver):**
- model/campo novo + `makemigrations` → `<app>/migrations/NNNN_*.py`

## 6. Multi-tenant (isolamento por Empresa)

- Como cada query desta feature é escopada pela(s) `Empresa`(s) do usuário (`get_empresas_filtradas` / `.filter(empresa__in=...)`).
- `get_object_or_404` escopado por empresa (sem IDOR).
- super_admin/staff: <vê tudo? / mesma regra?>

## 7. Critérios de aceite

<Gherkin em português. Cada um vira teste.>
- [ ] **DADO** <contexto> **QUANDO** <ação> **ENTÃO** <resultado esperado>
- [ ] **DADO** ... **QUANDO** ... **ENTÃO** ...

## 8. Testes (Django TestCase / pytest-django)

- `<app>/tests.py::test_<criterio_1>` — prova critério 1
- `<app>/tests.py::test_<criterio_2>` — prova critério 2
- Teste de isolamento: usuário da empresa A NÃO acessa registro da empresa B
- Teste de edge case: <cenário limite>

## 9. Riscos / decisões abertas

- <algo que pode dar errado, ou decisão que precisa do usuário>
