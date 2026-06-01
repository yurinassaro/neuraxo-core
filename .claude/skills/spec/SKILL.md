---
name: spec
description: Spec-Driven Development adaptado ao NeuraxoCheck (Django). Escreve uma spec formal ANTES de implementar uma feature/mudança — com regra de negócio, contrato de rotas/views, critérios de aceite e plano de camadas (URL → view fina → model/serviço → ORM). Use quando o usuário for começar uma feature nova, refatorar um módulo, ou pedir "cria a spec", "spec-driven", "planeja antes de codar".
---

# spec — Spec-Driven Development no NeuraxoCheck

Adaptação do método spec-driven (escrever a spec antes do código) para a realidade do NeuraxoCheck: **Django 5.2 + PostgreSQL, schema único multi-tenant por `Empresa`**, organizado em apps (`core`, `tenants`, `checklists`, `financeiro`, `jarvis`, `notifications`). Inspirado em OpenSpec/SDD, mas em português e no stack Django do projeto — sem ferramenta externa.

O objetivo é dar à IA (e ao humano) um **contrato claro antes de implementar**, para que o código gerado seja previsível, testável e não engorde a view. Specs ficam em `specs/` na raiz do projeto.

## Quando usar

- ✅ Feature nova de tamanho médio/grande (nova rota + lógica + model/migration)
- ✅ Refatorar uma view gorda (extrair lógica para método de model / serviço)
- ✅ Mudança que toca regra de negócio (checklist, demanda, financeiro, cofre, Jarvis)
- ❌ NÃO use para: typo, ajuste de CSS, mudança trivial de 1 linha, CRUD simples de 3 telas.

## Fluxo (4 fases)

### 1. EXPLORE — entender antes de propor
Antes de escrever a spec, levante o estado atual:
- Quais apps/views/models/tabelas a feature toca? (use grep/Read)
- Qual o padrão já usado em features parecidas? (ex: `checklists/views.py` é o app mais maduro; veja `get_empresas_filtradas` para o padrão de isolamento)
- Há memória/decisão relevante no `MEMORY.md` do projeto ou nos `checklists/`/`docs/`?
Resuma o que encontrou em 3-5 linhas. NÃO pule esta fase — spec sem contexto vira ficção.

### 2. PROPOSE — escrever a spec
Crie `specs/<NNN>-<nome-kebab>/spec.md` usando o template em `references/template-spec.md`. A spec DEVE conter:
- **Por quê** (problema/motivação) e **O quê** (escopo) — e o que está **fora de escopo**
- **Regra de negócio** em bullets verificáveis (não prosa vaga). Toda regra que vai pra produção tem 1 bullet aqui.
- **Contrato** das rotas: método, path (nome da URL), entrada (form/JSON), saída, códigos de status, e quem pode acessar (`@login_required` + papel exigido: gestor/colaborador/executante)
- **Plano de camadas** (obrigatório — é o coração do método): o que vai na view (fina), o que vai no model/serviço (lógica), que QuerySets/migration são necessários.
- **Multi-tenant**: como cada query é escopada pela(s) `Empresa`(s) do usuário (regra inegociável)
- **Critérios de aceite** no formato `DADO ... QUANDO ... ENTÃO ...` (Gherkin em português)
- **Testes** que provam cada critério (Django `TestCase`/pytest-django)

### 3. APPLY — implementar seguindo a spec
- Implemente na ordem das camadas: **model/migration/serviço primeiro, view por último** (a view só orquestra o que o model/serviço já faz).
- Rode `makemigrations` + `migrate` para mudanças de model.
- Cada critério de aceite vira pelo menos 1 teste.
- Ao terminar, rode os testes e marque os critérios cumpridos na spec (`- [x]`).
- Se durante a implementação a regra mudar, ATUALIZE a spec — a spec é a fonte da verdade, não o código.

### 4. ARCHIVE — fechar
- Confirme: todos os critérios `[x]`, testes passando, `/clean-check` PASS.
- Mova a spec para `specs/_done/` (ou marque `status: done` no topo).
- Registre a decisão na memória do projeto (`MEMORY.md`) se houve aprendizado não-óbvio.

## Regras de camada (inegociáveis no NeuraxoCheck)

Estas existem pra impedir a "view gorda" — `checklists/views.py` já tem 5000 linhas; novas features não devem piorar isso.

### As camadas (alvo arquitetural — stack Django)

```
URL (urls.py)  →  view (HTTP, fina)  →  model/serviço (regra)  →  ORM/QuerySet  →  banco
                       ↑
                  models.py: regras de domínio (métodos de model/manager,
                             enums/choices, máquinas de estado, validações)
```

1. **View fina** (`<app>/views.py`): a view valida auth/papel → carrega contexto escopado por empresa → chama método de model/serviço → render/redirect/JsonResponse. Sem regra de negócio densa.

2. **Model / serviço** (`<app>/models.py` ou um módulo `services.py`/função dedicada): a lógica de negócio. Métodos de model (`Pessoa.get_papel_empresa`), managers customizados, ou funções de domínio puras (validações, cálculos, máquinas de estado). Testável sem HTTP.

3. **ORM**: acesso a dados via QuerySet do Django, sempre escopado por empresa (ver abaixo). Evitar SQL cru; se inevitável, parametrizado.

### Regras de isolamento e segurança (sempre)

4. **Isolamento por `Empresa` em toda query de negócio** — usar `get_empresas_filtradas(pessoa, request)` + `.filter(empresa__in=...)` (ou via relação). Respeitar `empresa_ativa_id` da sessão. `get_object_or_404` de model multi-tenant DEVE escopar por empresa do usuário (evitar IDOR). super_admin/staff é a exceção consciente.
5. **Papéis por empresa**: gestor / colaborador / executante via `Pessoa.get_papel_empresa(empresa)`. Ação de gestão exige `is_gestor_empresa(empresa)`. `is_gestor` global é legado — não usar como única fonte.
6. **CSRF automático do Django** — forms usam `{% csrf_token %}`; webhooks isentos são conscientes e justificados.
7. **Segredos via env/settings** — API keys (Anthropic), chave Fernet do cofre, credenciais: nunca hardcoded. Cofre criptografa com Fernet.

### Migração incremental (não big-bang)

A cada feature/bug numa view gorda: extrair o pedaço para um método de model ou função de serviço; testar a lógica isolada (rede de segurança); validar no browser; commit pequeno. NÃO reorganizar o app inteiro de uma vez.

## Saída

Ao rodar esta skill, entregue a fase pedida. Se o usuário só disse "cria a spec de X", faça EXPLORE + PROPOSE e mostre a spec pra ele aprovar ANTES de implementar (APPLY). Não pule pra implementação sem a spec aprovada — esse é o ponto inteiro do método.

Veja `references/template-spec.md` para o formato exato da spec e `references/exemplo-spec.md` para um exemplo preenchido.
