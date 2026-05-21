"""
Jarvis AI - Definição de tools e executor para o NeuraxoCheck.
Cada tool é uma ação que o Claude pode executar no sistema.
"""
import json
from datetime import timedelta
from django.utils import timezone
from core.models import Empresa, Pessoa
from checklists.models import (
    ChecklistTemplate, Demanda, Projeto,
    PrioridadeDemanda, StatusDemanda, StatusProjeto,
)

# ============================================
# DEFINIÇÃO DAS TOOLS (enviadas ao Claude API)
# ============================================

TOOLS = [
    {
        "name": "criar_rotina",
        "description": (
            "Cria uma tarefa recorrente (rotina diária) no sistema. "
            "Exemplos: 'conferir estoque toda segunda', 'enviar relatório diariamente'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "titulo": {
                    "type": "string",
                    "description": "Nome da rotina. Ex: 'Conferir estoque'",
                },
                "empresa": {
                    "type": "string",
                    "description": "Nome da empresa. Ex: 'Tarragona', 'Neuraxo'",
                },
                "responsavel": {
                    "type": "string",
                    "description": "Nome do responsavel. Se nao informado, atribui ao usuario atual.",
                },
                "recorrencia": {
                    "type": "string",
                    "enum": ["diaria", "semanal", "quinzenal", "mensal"],
                    "description": "Frequencia da rotina. Padrao: diaria",
                },
                "dias_semana": {
                    "type": "string",
                    "description": (
                        "Dias da semana ativos separados por virgula. "
                        "0=Seg, 1=Ter, 2=Qua, 3=Qui, 4=Sex, 5=Sab, 6=Dom. "
                        "Ex: '0,2,4' para seg/qua/sex. Padrao: '0,1,2,3,4' (seg a sex)"
                    ),
                },
                "tempo_estimado": {
                    "type": "integer",
                    "description": "Tempo estimado em minutos. Opcoes: 15, 30, 45, 60, 90, 120, 180, 240",
                },
                "prioridade": {
                    "type": "integer",
                    "enum": [1, 2, 3],
                    "description": "1=Baixa, 2=Media, 3=Alta. Padrao: 1",
                },
                "descricao": {
                    "type": "string",
                    "description": "Descricao detalhada da rotina (opcional)",
                },
            },
            "required": ["titulo", "empresa"],
        },
    },
    {
        "name": "criar_demanda",
        "description": (
            "Cria uma demanda/pendencia com prazo. "
            "Exemplos: 'criar tarefa pra Andre entregar relatorio ate sexta', "
            "'pendencia urgente: ligar pro fornecedor amanha'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "titulo": {
                    "type": "string",
                    "description": "Titulo da demanda",
                },
                "empresa": {
                    "type": "string",
                    "description": "Nome da empresa",
                },
                "responsavel": {
                    "type": "string",
                    "description": "Nome do responsavel pela execucao",
                },
                "prazo": {
                    "type": "string",
                    "description": (
                        "Prazo no formato YYYY-MM-DD ou YYYY-MM-DD HH:MM. "
                        "Pode usar expressoes como 'amanha', 'sexta', 'em 3 dias'."
                    ),
                },
                "prioridade": {
                    "type": "string",
                    "enum": ["baixa", "media", "alta", "urgente"],
                    "description": "Prioridade da demanda. Padrao: media",
                },
                "descricao": {
                    "type": "string",
                    "description": "Descricao detalhada (opcional)",
                },
                "projeto": {
                    "type": "string",
                    "description": "Nome do projeto vinculado (opcional)",
                },
            },
            "required": ["titulo", "empresa", "prazo"],
        },
    },
    {
        "name": "criar_projeto",
        "description": (
            "Cria um novo projeto com etapas. "
            "Exemplos: 'criar projeto Redesign do Site na Neuraxo'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "titulo": {
                    "type": "string",
                    "description": "Titulo do projeto",
                },
                "empresa": {
                    "type": "string",
                    "description": "Nome da empresa",
                },
                "responsavel": {
                    "type": "string",
                    "description": "Nome do responsavel/lider do projeto",
                },
                "prazo": {
                    "type": "string",
                    "description": "Prazo geral no formato YYYY-MM-DD (opcional)",
                },
                "descricao": {
                    "type": "string",
                    "description": "Descricao do projeto (opcional)",
                },
            },
            "required": ["titulo", "empresa"],
        },
    },
    {
        "name": "listar_pendencias",
        "description": (
            "Lista demandas/pendencias abertas. Pode filtrar por empresa, responsavel ou status. "
            "Exemplos: 'quais pendencias do Andre?', 'demandas atrasadas da Tarragona'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "empresa": {
                    "type": "string",
                    "description": "Filtrar por empresa (opcional)",
                },
                "responsavel": {
                    "type": "string",
                    "description": "Filtrar por responsavel (opcional)",
                },
                "status": {
                    "type": "string",
                    "enum": ["pendente", "em_andamento", "atrasadas", "todas"],
                    "description": "Filtrar por status. Padrao: todas abertas",
                },
                "limite": {
                    "type": "integer",
                    "description": "Quantidade maxima de resultados. Padrao: 10",
                },
            },
            "required": [],
        },
    },
    {
        "name": "resumo_dia",
        "description": (
            "Mostra resumo do dia: tarefas concluidas, pendentes, aproveitamento. "
            "Exemplos: 'como foi meu dia?', 'resumo de hoje', 'aproveitamento do Andre'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pessoa": {
                    "type": "string",
                    "description": "Nome da pessoa (opcional, padrao: usuario atual)",
                },
                "empresa": {
                    "type": "string",
                    "description": "Filtrar por empresa (opcional)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "concluir_tarefa",
        "description": (
            "Marca uma demanda como concluida pelo titulo ou ID. "
            "Exemplos: 'concluir tarefa ligar pro fornecedor', 'fechar demanda #42'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "titulo_ou_id": {
                    "type": "string",
                    "description": "Titulo (busca parcial) ou ID numerico da demanda",
                },
                "empresa": {
                    "type": "string",
                    "description": "Empresa para desambiguar se houver mais de uma (opcional)",
                },
            },
            "required": ["titulo_ou_id"],
        },
    },
    {
        "name": "excluir_rotina",
        "description": (
            "Exclui uma rotina diaria (ChecklistTemplate). SEMPRE chame primeiro com confirmado=false "
            "para mostrar os detalhes ao usuario e pedir confirmacao. So chame com confirmado=true "
            "quando o usuario confirmar explicitamente. "
            "Exemplos: 'exclui a rotina conferir estoque', 'remove a rotina #5'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "titulo_ou_id": {
                    "type": "string",
                    "description": "Titulo (busca parcial) ou ID numerico da rotina",
                },
                "empresa": {
                    "type": "string",
                    "description": "Empresa para desambiguar (opcional)",
                },
                "confirmado": {
                    "type": "boolean",
                    "description": "false=mostrar detalhes e pedir confirmacao, true=excluir de fato",
                },
            },
            "required": ["titulo_ou_id"],
        },
    },
    {
        "name": "excluir_demanda",
        "description": (
            "Exclui uma demanda/pendencia. SEMPRE chame primeiro com confirmado=false "
            "para mostrar os detalhes ao usuario e pedir confirmacao. So chame com confirmado=true "
            "quando o usuario confirmar explicitamente. "
            "Exemplos: 'exclui a demanda ligar pro fornecedor', 'apaga pendencia #42'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "titulo_ou_id": {
                    "type": "string",
                    "description": "Titulo (busca parcial) ou ID numerico da demanda",
                },
                "empresa": {
                    "type": "string",
                    "description": "Empresa para desambiguar (opcional)",
                },
                "confirmado": {
                    "type": "boolean",
                    "description": "false=mostrar detalhes e pedir confirmacao, true=excluir de fato",
                },
            },
            "required": ["titulo_ou_id"],
        },
    },
    {
        "name": "excluir_projeto",
        "description": (
            "Exclui um projeto e todas as suas demandas/etapas. SEMPRE chame primeiro com confirmado=false "
            "para mostrar os detalhes ao usuario e pedir confirmacao. So chame com confirmado=true "
            "quando o usuario confirmar explicitamente. "
            "Exemplos: 'exclui o projeto Redesign', 'remove projeto #10'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "titulo_ou_id": {
                    "type": "string",
                    "description": "Titulo (busca parcial) ou ID numerico do projeto",
                },
                "empresa": {
                    "type": "string",
                    "description": "Empresa para desambiguar (opcional)",
                },
                "confirmado": {
                    "type": "boolean",
                    "description": "false=mostrar detalhes e pedir confirmacao, true=excluir de fato",
                },
            },
            "required": ["titulo_ou_id"],
        },
    },
]


# ============================================
# EXECUTOR - mapeia tool_calls para ações
# ============================================

def _find_empresa(nome, pessoa):
    """Busca empresa pelo nome entre as empresas do usuario."""
    empresas = pessoa.empresas.filter(ativo=True)
    # Busca exata
    match = empresas.filter(nome__iexact=nome).first()
    if match:
        return match
    # Busca parcial
    match = empresas.filter(nome__icontains=nome).first()
    if match:
        return match
    nomes = list(empresas.values_list('nome', flat=True))
    return None, nomes


def _find_pessoa(nome, empresa):
    """Busca pessoa pelo nome dentro de uma empresa."""
    pessoas = Pessoa.objects.filter(empresas=empresa, ativo=True)
    match = pessoas.filter(nome__icontains=nome).first()
    if match:
        return match
    nomes = list(pessoas.values_list('nome', flat=True))
    return None, nomes


def _check_gestor(pessoa, empresa):
    """Verifica se a pessoa é gestora da empresa. Retorna mensagem de erro ou None."""
    if not pessoa.is_gestor_empresa(empresa):
        return f"Sem permissao. Voce nao e gestor da empresa {empresa.nome}."
    return None


def executar_tool(tool_name, tool_input, pessoa):
    """Executa uma tool e retorna o resultado como string."""
    executors = {
        'criar_rotina': _exec_criar_rotina,
        'criar_demanda': _exec_criar_demanda,
        'criar_projeto': _exec_criar_projeto,
        'listar_pendencias': _exec_listar_pendencias,
        'resumo_dia': _exec_resumo_dia,
        'concluir_tarefa': _exec_concluir_tarefa,
        'excluir_rotina': _exec_excluir_rotina,
        'excluir_demanda': _exec_excluir_demanda,
        'excluir_projeto': _exec_excluir_projeto,
    }
    executor = executors.get(tool_name)
    if not executor:
        return f"Tool '{tool_name}' nao reconhecida."
    return executor(tool_input, pessoa)


def _exec_criar_rotina(inp, pessoa):
    empresa_result = _find_empresa(inp['empresa'], pessoa)
    if isinstance(empresa_result, tuple):
        _, nomes = empresa_result
        return f"Empresa '{inp['empresa']}' nao encontrada. Suas empresas: {', '.join(nomes)}"
    empresa = empresa_result

    # Apenas gestores podem criar rotinas
    erro = _check_gestor(pessoa, empresa)
    if erro:
        return erro

    # Responsavel
    responsavel = pessoa
    if inp.get('responsavel'):
        resp_result = _find_pessoa(inp['responsavel'], empresa)
        if isinstance(resp_result, tuple):
            _, nomes = resp_result
            return f"Pessoa '{inp['responsavel']}' nao encontrada na {empresa.nome}. Pessoas: {', '.join(nomes)}"
        responsavel = resp_result

    rotina = ChecklistTemplate.objects.create(
        empresa=empresa,
        titulo=inp['titulo'],
        descricao=inp.get('descricao', ''),
        recorrencia=inp.get('recorrencia', 'diaria'),
        dias_semana_ativos=inp.get('dias_semana', '0,1,2,3,4'),
        responsavel=responsavel,
        tempo_estimado=inp.get('tempo_estimado', 0),
        prioridade=inp.get('prioridade', 1),
        ativo=True,
    )
    dias_map = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sab', 6: 'Dom'}
    dias = [dias_map.get(int(d), d) for d in rotina.dias_semana_ativos.split(',') if d.strip()]
    return (
        f"Rotina criada com sucesso!\n"
        f"- Titulo: {rotina.titulo}\n"
        f"- Empresa: {empresa.nome}\n"
        f"- Responsavel: {responsavel.nome}\n"
        f"- Recorrencia: {rotina.recorrencia}\n"
        f"- Dias: {', '.join(dias)}\n"
        f"- ID: #{rotina.id}"
    )


def _exec_criar_demanda(inp, pessoa):
    empresa_result = _find_empresa(inp['empresa'], pessoa)
    if isinstance(empresa_result, tuple):
        _, nomes = empresa_result
        return f"Empresa '{inp['empresa']}' nao encontrada. Suas empresas: {', '.join(nomes)}"
    empresa = empresa_result

    # Apenas gestores podem criar demandas
    erro = _check_gestor(pessoa, empresa)
    if erro:
        return erro

    # Responsavel
    responsavel = pessoa
    if inp.get('responsavel'):
        resp_result = _find_pessoa(inp['responsavel'], empresa)
        if isinstance(resp_result, tuple):
            _, nomes = resp_result
            return f"Pessoa '{inp['responsavel']}' nao encontrada na {empresa.nome}. Pessoas: {', '.join(nomes)}"
        responsavel = resp_result

    # Prazo - tenta parsear
    from django.utils.dateparse import parse_datetime, parse_date
    prazo_str = inp['prazo']
    prazo = parse_datetime(prazo_str)
    if not prazo:
        dt = parse_date(prazo_str)
        if dt:
            prazo = timezone.make_aware(
                timezone.datetime.combine(dt, timezone.datetime.min.replace(hour=18).time())
            )
    if not prazo:
        return f"Nao consegui interpretar o prazo '{prazo_str}'. Use o formato YYYY-MM-DD ou YYYY-MM-DD HH:MM."

    # Projeto vinculado
    projeto = None
    if inp.get('projeto'):
        projeto = Projeto.objects.filter(
            empresa=empresa, titulo__icontains=inp['projeto']
        ).first()

    demanda = Demanda.objects.create(
        empresa=empresa,
        titulo=inp['titulo'],
        descricao=inp.get('descricao', ''),
        responsavel=responsavel,
        solicitante=pessoa,
        prazo=prazo,
        prioridade=inp.get('prioridade', 'media'),
        projeto=projeto,
    )
    return (
        f"Demanda criada com sucesso!\n"
        f"- Titulo: {demanda.titulo}\n"
        f"- Empresa: {empresa.nome}\n"
        f"- Responsavel: {responsavel.nome}\n"
        f"- Prazo: {demanda.prazo.strftime('%d/%m/%Y %H:%M')}\n"
        f"- Prioridade: {demanda.prioridade}\n"
        f"- ID: #{demanda.id}"
    )


def _exec_criar_projeto(inp, pessoa):
    empresa_result = _find_empresa(inp['empresa'], pessoa)
    if isinstance(empresa_result, tuple):
        _, nomes = empresa_result
        return f"Empresa '{inp['empresa']}' nao encontrada. Suas empresas: {', '.join(nomes)}"
    empresa = empresa_result

    # Apenas gestores podem criar projetos
    erro = _check_gestor(pessoa, empresa)
    if erro:
        return erro

    responsavel = pessoa
    if inp.get('responsavel'):
        resp_result = _find_pessoa(inp['responsavel'], empresa)
        if isinstance(resp_result, tuple):
            _, nomes = resp_result
            return f"Pessoa '{inp['responsavel']}' nao encontrada na {empresa.nome}. Pessoas: {', '.join(nomes)}"
        responsavel = resp_result

    prazo = None
    if inp.get('prazo'):
        from django.utils.dateparse import parse_date
        prazo = parse_date(inp['prazo'])

    projeto = Projeto.objects.create(
        empresa=empresa,
        titulo=inp['titulo'],
        descricao=inp.get('descricao', ''),
        responsavel=responsavel,
        prazo=prazo,
        status=StatusProjeto.PLANEJAMENTO,
    )
    return (
        f"Projeto criado com sucesso!\n"
        f"- Titulo: {projeto.titulo}\n"
        f"- Empresa: {empresa.nome}\n"
        f"- Responsavel: {responsavel.nome}\n"
        f"- Status: Planejamento\n"
        f"- ID: #{projeto.id}"
    )


def _exec_listar_pendencias(inp, pessoa):
    qs = Demanda.objects.exclude(status__in=['concluido', 'cancelado'])

    # Filtra por empresas do usuario
    empresas_usuario = pessoa.empresas.filter(ativo=True)
    qs = qs.filter(empresa__in=empresas_usuario)

    # Funcionario so ve as proprias pendencias (gestor ve todas)
    if not pessoa.eh_gestor:
        qs = qs.filter(responsavel=pessoa)

    if inp.get('empresa'):
        empresa_result = _find_empresa(inp['empresa'], pessoa)
        if not isinstance(empresa_result, tuple):
            qs = qs.filter(empresa=empresa_result)

    if inp.get('responsavel') and pessoa.eh_gestor:
        qs = qs.filter(responsavel__nome__icontains=inp['responsavel'])

    status_filter = inp.get('status', 'todas')
    if status_filter == 'atrasadas':
        qs = qs.filter(prazo__lt=timezone.now())
    elif status_filter in ['pendente', 'em_andamento']:
        qs = qs.filter(status=status_filter)

    limite = inp.get('limite', 10)
    demandas = qs.order_by('-prioridade', 'prazo')[:limite]

    if not demandas:
        return "Nenhuma pendencia encontrada com esses filtros."

    linhas = [f"**{demandas.count()} pendencia(s) encontrada(s):**\n"]
    for d in demandas:
        atrasada = " [ATRASADA]" if d.esta_atrasada() else ""
        linhas.append(
            f"- **#{d.id}** {d.titulo} | {d.empresa.nome} | "
            f"{d.responsavel.nome if d.responsavel else 'Sem resp.'} | "
            f"Prazo: {d.prazo.strftime('%d/%m/%Y')} | "
            f"{d.get_prioridade_display()}{atrasada}"
        )
    return "\n".join(linhas)


def _exec_resumo_dia(inp, pessoa):
    from checklists.models import ChecklistItem

    # Pessoa alvo
    alvo = pessoa
    if inp.get('pessoa'):
        match = Pessoa.objects.filter(nome__icontains=inp['pessoa'], ativo=True).first()
        if match:
            # Funcionario so ve o proprio resumo
            if match != pessoa and not pessoa.eh_gestor:
                return f"Sem permissao para ver o resumo de {match.nome}."
            alvo = match

    hoje = timezone.localdate()
    items_hoje = ChecklistItem.objects.filter(
        responsavel=alvo,
        data_referencia=hoje,
    )
    total = items_hoje.count()
    concluidos = items_hoje.filter(status='concluido').count()
    pct = int((concluidos / total) * 100) if total > 0 else 0

    # Demandas do dia
    demandas_abertas = Demanda.objects.filter(
        responsavel=alvo,
    ).exclude(status__in=['concluido', 'cancelado']).count()
    demandas_atrasadas = Demanda.objects.filter(
        responsavel=alvo,
        prazo__lt=timezone.now(),
    ).exclude(status__in=['concluido', 'cancelado']).count()

    # Tempo trabalhado
    tempo_total = sum(i.get_tempo_total() for i in items_hoje)
    horas = tempo_total // 3600
    minutos = (tempo_total % 3600) // 60

    return (
        f"**Resumo de {alvo.nome} - {hoje.strftime('%d/%m/%Y')}**\n\n"
        f"**Rotina Diaria:**\n"
        f"- Tarefas: {concluidos}/{total} concluidas ({pct}%)\n"
        f"- Tempo trabalhado: {horas}h{minutos:02d}min\n\n"
        f"**Pendencias:**\n"
        f"- Abertas: {demandas_abertas}\n"
        f"- Atrasadas: {demandas_atrasadas}"
    )


def _exec_concluir_tarefa(inp, pessoa):
    titulo_ou_id = inp['titulo_ou_id'].strip()
    empresas_usuario = pessoa.empresas.filter(ativo=True)

    # Busca por ID
    if titulo_ou_id.startswith('#'):
        titulo_ou_id = titulo_ou_id[1:]
    if titulo_ou_id.isdigit():
        demanda = Demanda.objects.filter(id=int(titulo_ou_id), empresa__in=empresas_usuario).first()
    else:
        qs = Demanda.objects.filter(
            titulo__icontains=titulo_ou_id,
            empresa__in=empresas_usuario,
        ).exclude(status__in=['concluido', 'cancelado'])
        if inp.get('empresa'):
            empresa_result = _find_empresa(inp['empresa'], pessoa)
            if not isinstance(empresa_result, tuple):
                qs = qs.filter(empresa=empresa_result)
        if qs.count() > 1:
            opcoes = "\n".join(f"- #{d.id} {d.titulo} ({d.empresa.nome})" for d in qs[:5])
            return f"Encontrei mais de uma demanda. Qual delas?\n{opcoes}"
        demanda = qs.first()

    if not demanda:
        return f"Demanda '{inp['titulo_ou_id']}' nao encontrada."

    # Permissao: responsavel pode concluir a propria, gestor pode concluir qualquer uma
    if demanda.responsavel != pessoa and not pessoa.is_gestor_empresa(demanda.empresa):
        return f"Sem permissao. Essa demanda e do {demanda.responsavel.nome if demanda.responsavel else 'sem responsavel'}."

    if demanda.status == 'concluido':
        return f"A demanda #{demanda.id} '{demanda.titulo}' ja esta concluida."

    demanda.status = StatusDemanda.CONCLUIDO
    demanda.concluido_em = timezone.now()
    if demanda.timer_ativo:
        demanda.pausar_timer()
    demanda.save()
    return f"Demanda #{demanda.id} '{demanda.titulo}' marcada como concluida!"


def _find_item_by_titulo_ou_id(Model, titulo_ou_id, pessoa, empresa_nome=None):
    """Busca genérica por titulo ou ID dentro das empresas do usuario."""
    titulo_ou_id = titulo_ou_id.strip().lstrip('#')
    empresas_usuario = pessoa.empresas.filter(ativo=True)

    if titulo_ou_id.isdigit():
        item = Model.objects.filter(id=int(titulo_ou_id), empresa__in=empresas_usuario).first()
        if item:
            return item
        return None, "Nao encontrado com esse ID."

    qs = Model.objects.filter(titulo__icontains=titulo_ou_id, empresa__in=empresas_usuario)
    if empresa_nome:
        empresa_result = _find_empresa(empresa_nome, pessoa)
        if not isinstance(empresa_result, tuple):
            qs = qs.filter(empresa=empresa_result)

    if qs.count() == 0:
        return None, f"Nenhum resultado encontrado para '{titulo_ou_id}'."
    if qs.count() > 1:
        opcoes = "\n".join(f"- #{i.id} {i.titulo} ({i.empresa.nome})" for i in qs[:5])
        return None, f"Encontrei mais de um. Qual deles?\n{opcoes}"
    return qs.first()


def _exec_excluir_rotina(inp, pessoa):
    result = _find_item_by_titulo_ou_id(ChecklistTemplate, inp['titulo_ou_id'], pessoa, inp.get('empresa'))
    if isinstance(result, tuple):
        _, msg = result
        return msg
    rotina = result

    # Apenas gestores podem excluir rotinas
    erro = _check_gestor(pessoa, rotina.empresa)
    if erro:
        return erro

    confirmado = inp.get('confirmado', False)

    if not confirmado:
        return (
            f"CONFIRMACAO NECESSARIA - Vou excluir a rotina:\n"
            f"- ID: #{rotina.id}\n"
            f"- Titulo: {rotina.titulo}\n"
            f"- Empresa: {rotina.empresa.nome}\n"
            f"- Responsavel: {rotina.responsavel.nome if rotina.responsavel else 'Todos'}\n"
            f"- Recorrencia: {rotina.recorrencia}\n"
            f"Isso vai excluir tambem todas as tarefas geradas por essa rotina. "
            f"Peca confirmacao ao usuario antes de prosseguir."
        )

    titulo = rotina.titulo
    empresa = rotina.empresa.nome
    rotina.delete()
    return f"Rotina '{titulo}' ({empresa}) excluida com sucesso!"


def _exec_excluir_demanda(inp, pessoa):
    result = _find_item_by_titulo_ou_id(Demanda, inp['titulo_ou_id'], pessoa, inp.get('empresa'))
    if isinstance(result, tuple):
        _, msg = result
        return msg
    demanda = result

    # Apenas gestores podem excluir demandas
    erro = _check_gestor(pessoa, demanda.empresa)
    if erro:
        return erro

    confirmado = inp.get('confirmado', False)

    if not confirmado:
        return (
            f"CONFIRMACAO NECESSARIA - Vou excluir a demanda:\n"
            f"- ID: #{demanda.id}\n"
            f"- Titulo: {demanda.titulo}\n"
            f"- Empresa: {demanda.empresa.nome}\n"
            f"- Responsavel: {demanda.responsavel.nome if demanda.responsavel else 'Sem resp.'}\n"
            f"- Prazo: {demanda.prazo.strftime('%d/%m/%Y')}\n"
            f"- Status: {demanda.status}\n"
            f"Peca confirmacao ao usuario antes de prosseguir."
        )

    titulo = demanda.titulo
    empresa = demanda.empresa.nome
    demanda.delete()
    return f"Demanda '{titulo}' ({empresa}) excluida com sucesso!"


def _exec_excluir_projeto(inp, pessoa):
    result = _find_item_by_titulo_ou_id(Projeto, inp['titulo_ou_id'], pessoa, inp.get('empresa'))
    if isinstance(result, tuple):
        _, msg = result
        return msg
    projeto = result

    # Apenas gestores podem excluir projetos
    erro = _check_gestor(pessoa, projeto.empresa)
    if erro:
        return erro

    confirmado = inp.get('confirmado', False)

    total_demandas = projeto.demandas.count()

    if not confirmado:
        return (
            f"CONFIRMACAO NECESSARIA - Vou excluir o projeto:\n"
            f"- ID: #{projeto.id}\n"
            f"- Titulo: {projeto.titulo}\n"
            f"- Empresa: {projeto.empresa.nome}\n"
            f"- Responsavel: {projeto.responsavel.nome if projeto.responsavel else 'Sem resp.'}\n"
            f"- Demandas vinculadas: {total_demandas}\n"
            f"- Status: {projeto.status}\n"
            f"As demandas vinculadas serao desvinculadas (nao excluidas). "
            f"Peca confirmacao ao usuario antes de prosseguir."
        )

    titulo = projeto.titulo
    empresa = projeto.empresa.nome
    projeto.delete()
    return f"Projeto '{titulo}' ({empresa}) excluido com sucesso! {total_demandas} demanda(s) desvinculadas."
