from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Q, Sum, Avg
from django.db.models.functions import Coalesce
from .models import (
    ChecklistItem, ChecklistTemplate, StatusItem, SubTarefa, SubTarefaTemplate,
    Demanda, SubTarefaDemanda, AnexoDemanda, ComentarioDemanda,
    StatusDemanda, PrioridadeDemanda, AproveitamentoDiario,
    Projeto, StatusProjeto, ProjetoTemplate, TipoEtapa,
    MapaMentalNo, TipoNoMapa, Anotacao,
)
from django.conf import settings
from core.models import Pessoa, Empresa, Cliente, ItemCofre, CategoriaCofre, PastaEmpresa, ArquivoEmpresa
from datetime import timedelta, date, datetime
from calendar import monthrange
import json
import calendar


def get_pessoa_or_redirect(request):
    """Helper para obter pessoa do usuário ou redirecionar"""
    try:
        return request.user.pessoa
    except Pessoa.DoesNotExist:
        return None


def get_empresas_filtradas(pessoa, request):
    """Retorna empresas filtradas pela empresa ativa na sessão.
    Se empresa_ativa_id está na sessão, filtra para ela.
    Se não, retorna todas as empresas da pessoa."""
    empresa_ativa_id = request.session.get('empresa_ativa_id')
    if empresa_ativa_id:
        filtradas = pessoa.empresas.filter(id=empresa_ativa_id, ativo=True)
        if filtradas.exists():
            return filtradas
    return pessoa.empresas.filter(ativo=True)


@login_required
def dashboard(request):
    """Dashboard principal - visão geral completa"""
    hoje = timezone.localdate()
    agora = timezone.now()
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa:
        messages.warning(request, 'Seu usuário não está vinculado a uma pessoa. Contate o administrador.')
        return render(request, 'checklists/sem_vinculo.html')

    # ========== DADOS DO USUÁRIO ==========
    empresas_filtro = get_empresas_filtradas(pessoa, request)

    # Tarefas do dia
    minhas_tarefas = ChecklistItem.objects.filter(
        responsavel=pessoa,
        data_referencia=hoje,
        template__empresa__in=empresas_filtro,
    ).select_related('template', 'template__empresa')

    total_tarefas = minhas_tarefas.count()
    tarefas_concluidas = minhas_tarefas.filter(status=StatusItem.CONCLUIDO).count()
    aproveitamento_hoje = int((tarefas_concluidas / total_tarefas) * 100) if total_tarefas > 0 else 0

    # Tarefas não concluídas (para lista)
    tarefas_pendentes = minhas_tarefas.exclude(status=StatusItem.CONCLUIDO).order_by('ordem', 'template__ordem_execucao')

    # Minhas demandas abertas
    minhas_demandas = Demanda.objects.filter(
        responsavel=pessoa,
        empresa__in=empresas_filtro,
    ).exclude(status=StatusDemanda.CONCLUIDO).select_related('empresa')

    demandas_atrasadas = minhas_demandas.filter(prazo__lt=agora)
    demandas_urgentes = minhas_demandas.filter(
        prazo__gte=agora,
        prazo__lte=agora + timedelta(days=2)
    ).exclude(id__in=demandas_atrasadas)

    # Pendentes de justificativa
    pendentes_justificativa = ChecklistItem.objects.filter(
        responsavel=pessoa,
        dia_fechado=True,
        justificativa='',
        template__empresa__in=empresas_filtro,
    ).exclude(status=StatusItem.CONCLUIDO).count()

    # Aproveitamento últimos 7 dias
    ultimos_7_dias = []
    for i in range(6, -1, -1):
        data = hoje - timedelta(days=i)
        aprov = AproveitamentoDiario.objects.filter(pessoa=pessoa, data=data).first()
        ultimos_7_dias.append({
            'data': data,
            'dia': data.strftime('%a'),
            'percentual': float(aprov.percentual) if aprov else None,
            'concluidas': aprov.tarefas_concluidas if aprov else 0,
            'total': aprov.total_tarefas if aprov else 0,
        })

    # Tempo trabalhado hoje
    tempo_hoje = sum(t.get_tempo_total() for t in minhas_tarefas)
    horas_hoje = tempo_hoje // 3600
    minutos_hoje = (tempo_hoje % 3600) // 60

    # ========== DADOS DO GESTOR ==========
    equipe_stats = None
    demandas_equipe = None
    empresas = get_empresas_filtradas(pessoa, request)
    empresa_selecionada = None

    if pessoa.eh_gestor:
        # Filtro por empresa
        empresa_id = request.GET.get('empresa')
        if empresa_id:
            empresa_selecionada = empresas.filter(id=empresa_id).first()

        empresas_filtro = [empresa_selecionada] if empresa_selecionada else empresas

        # Estatísticas da equipe (filtrada por empresa)
        pessoas_equipe = Pessoa.objects.filter(
            empresas__in=empresas_filtro,
            ativo=True
        ).distinct().exclude(id=pessoa.id)

        equipe_stats = []
        for p in pessoas_equipe:
            tarefas_p = ChecklistItem.objects.filter(responsavel=p, data_referencia=hoje)
            if empresa_selecionada:
                tarefas_p = tarefas_p.filter(template__empresa=empresa_selecionada)
            total_p = tarefas_p.count()
            concluidas_p = tarefas_p.filter(status=StatusItem.CONCLUIDO).count()
            percentual_p = int((concluidas_p / total_p) * 100) if total_p > 0 else 0

            demandas_p = Demanda.objects.filter(responsavel=p).exclude(status=StatusDemanda.CONCLUIDO)
            if empresa_selecionada:
                demandas_p = demandas_p.filter(empresa=empresa_selecionada)
            atrasadas_p = demandas_p.filter(prazo__lt=agora).count()

            equipe_stats.append({
                'pessoa': p,
                'tarefas_total': total_p,
                'tarefas_concluidas': concluidas_p,
                'aproveitamento': percentual_p,
                'demandas_abertas': demandas_p.count(),
                'demandas_atrasadas': atrasadas_p,
            })

        # Ordenar por aproveitamento (menor primeiro para alertar)
        equipe_stats.sort(key=lambda x: x['aproveitamento'])

        # Aproveitamento médio da equipe
        if equipe_stats:
            aproveitamento_medio = sum(e['aproveitamento'] for e in equipe_stats) // len(equipe_stats)
        else:
            aproveitamento_medio = 0

        # Projetos ativos do gestor
        meus_projetos = Projeto.objects.filter(
            empresa__in=empresas_filtro,
            status__in=[StatusProjeto.PLANEJAMENTO, StatusProjeto.EM_ANDAMENTO],
        ).select_related('empresa', 'responsavel')[:5]

        # Demandas das empresas filtradas
        demandas_equipe = Demanda.objects.filter(
            empresa__in=empresas_filtro
        ).exclude(status=StatusDemanda.CONCLUIDO).select_related('empresa', 'responsavel').order_by('prazo')[:10]

    # ========== DEPENDÊNCIAS DE MIM (outros esperando por mim) ==========
    dependencias_de_mim_tarefas = ChecklistItem.objects.filter(
        dependente_de=pessoa,
        status=StatusItem.DEPENDENTE,
    ).select_related('template', 'template__empresa', 'responsavel').order_by('-data_referencia')

    dependencias_de_mim_demandas = Demanda.objects.filter(
        dependente_de=pessoa,
        status=StatusDemanda.DEPENDENTE,
    ).select_related('empresa', 'responsavel').order_by('prazo')

    total_dependencias_de_mim = dependencias_de_mim_tarefas.count() + dependencias_de_mim_demandas.count()

    # ========== ALERTAS ==========
    alertas = []

    if demandas_atrasadas.exists():
        alertas.append({
            'tipo': 'danger',
            'icone': 'exclamation-circle',
            'titulo': f'{demandas_atrasadas.count()} demanda(s) atrasada(s)',
            'link': '{% url "lista_demandas" %}',
        })

    if pendentes_justificativa > 0:
        alertas.append({
            'tipo': 'warning',
            'icone': 'document-text',
            'titulo': f'{pendentes_justificativa} tarefa(s) pendente(s) de justificativa',
            'link': '{% url "pendentes_justificativa" %}',
        })

    if aproveitamento_hoje < 50 and total_tarefas > 0 and tarefas_pendentes.exists():
        alertas.append({
            'tipo': 'info',
            'icone': 'clock',
            'titulo': f'Aproveitamento do dia: {aproveitamento_hoje}%',
            'link': '{% url "rotina_diaria" %}',
        })

    context = {
        'pessoa': pessoa,
        'hoje': hoje,
        'empresas': empresas,

        # Minhas tarefas
        'total_tarefas': total_tarefas,
        'tarefas_concluidas': tarefas_concluidas,
        'tarefas_pendentes': tarefas_pendentes[:5],
        'aproveitamento_hoje': aproveitamento_hoje,
        'tempo_hoje': f'{horas_hoje}h {minutos_hoje}m',

        # Minhas demandas
        'minhas_demandas': minhas_demandas[:5],
        'demandas_atrasadas': demandas_atrasadas,
        'demandas_urgentes': demandas_urgentes,
        'total_demandas': minhas_demandas.count(),

        # Histórico
        'ultimos_7_dias': ultimos_7_dias,
        'pendentes_justificativa': pendentes_justificativa,

        # Alertas
        'alertas': alertas,

        # Dependências de mim
        'dependencias_de_mim_tarefas': dependencias_de_mim_tarefas,
        'dependencias_de_mim_demandas': dependencias_de_mim_demandas,
        'total_dependencias_de_mim': total_dependencias_de_mim,

        # Gestor
        'equipe_stats': equipe_stats,
        'demandas_equipe': demandas_equipe,
        'empresa_selecionada': empresa_selecionada,
        'meus_projetos': meus_projetos if pessoa.eh_gestor else None,
        'aproveitamento_medio': aproveitamento_medio if pessoa.eh_gestor and equipe_stats else None,
    }
    return render(request, 'checklists/dashboard.html', context)


@login_required
def rotina_diaria(request):
    """Rotina diária - todas as tarefas do dia em ordem sequencial"""
    hoje = timezone.localdate()
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa:
        return redirect('dashboard')

    # Filtros
    status_filter = request.GET.get('status', '')
    empresas_filtro = get_empresas_filtradas(pessoa, request)

    # Pega tarefas das empresas filtradas
    items = ChecklistItem.objects.filter(
        responsavel=pessoa,
        data_referencia=hoje,
        template__empresa__in=empresas_filtro,
    ).select_related('template', 'template__empresa').order_by('ordem', 'template__ordem_execucao')

    if status_filter:
        items = items.filter(status=status_filter)

    # Progresso do dia
    total = items.count()
    concluidas = items.filter(status=StatusItem.CONCLUIDO).count()
    em_standby = items.filter(status=StatusItem.DEPENDENTE).count()
    progresso = int((concluidas / total) * 100) if total > 0 else 0

    # Separar tarefas por status
    tarefas_ativas = [i for i in items if i.status not in (StatusItem.DEPENDENTE, StatusItem.CONCLUIDO, StatusItem.EM_ANDAMENTO, StatusItem.CANCELADO)]
    tarefas_em_andamento = [i for i in items if i.status == StatusItem.EM_ANDAMENTO]
    tarefas_concluidas = [i for i in items if i.status == StatusItem.CONCLUIDO]
    tarefas_standby = [i for i in items if i.status == StatusItem.DEPENDENTE]
    tarefas_canceladas = [i for i in items if i.status == StatusItem.CANCELADO]

    # Demandas/pendências vencendo hoje (urgências)
    from datetime import datetime, time
    inicio_hoje = timezone.make_aware(datetime.combine(hoje, time.min))
    fim_hoje = timezone.make_aware(datetime.combine(hoje, time.max))

    if pessoa.eh_gestor:
        empresas_pessoa = get_empresas_filtradas(pessoa, request)
        urgencias_hoje = Demanda.objects.filter(
            empresa__in=empresas_pessoa,
            prazo__range=(inicio_hoje, fim_hoje),
        ).exclude(
            status__in=[StatusDemanda.CONCLUIDO, StatusDemanda.CANCELADO]
        ).select_related('responsavel', 'empresa').order_by('-prioridade', 'prazo')
    else:
        urgencias_hoje = Demanda.objects.filter(
            responsavel=pessoa,
            prazo__range=(inicio_hoje, fim_hoje),
        ).exclude(
            status__in=[StatusDemanda.CONCLUIDO, StatusDemanda.CANCELADO]
        ).select_related('responsavel', 'empresa').order_by('-prioridade', 'prazo')

    # Demandas atrasadas (prazo já passou)
    amanha = hoje + timedelta(days=1)
    inicio_amanha = timezone.make_aware(datetime.combine(amanha, time.min))
    fim_amanha = timezone.make_aware(datetime.combine(amanha, time.max))

    base_qs = Demanda.objects.exclude(
        status__in=[StatusDemanda.CONCLUIDO, StatusDemanda.CANCELADO]
    ).select_related('responsavel', 'empresa', 'projeto')

    if pessoa.eh_gestor:
        empresas_pessoa = get_empresas_filtradas(pessoa, request)
        filtro = Q(empresa__in=empresas_pessoa)
    else:
        filtro = Q(responsavel=pessoa)

    # Todas as atrasadas e vencendo
    todas_atrasadas = base_qs.filter(filtro, prazo__lt=inicio_hoje).order_by('prazo')
    todas_vencendo_amanha = base_qs.filter(filtro, prazo__range=(inicio_amanha, fim_amanha)).order_by('-prioridade', 'prazo')

    # Separar: demandas normais vs etapas de projeto
    atrasadas = [d for d in todas_atrasadas if not d.projeto_id]
    atrasadas_projeto = [d for d in todas_atrasadas if d.projeto_id]

    urgencias_hoje_list = list(urgencias_hoje)
    urgencias_hoje_normal = [d for d in urgencias_hoje_list if not d.projeto_id]
    urgencias_hoje_projeto = [d for d in urgencias_hoje_list if d.projeto_id]

    vencendo_amanha = [d for d in todas_vencendo_amanha if not d.projeto_id]
    vencendo_amanha_projeto = [d for d in todas_vencendo_amanha if d.projeto_id]

    # Demandas de projeto pendentes (não atrasadas, não vencendo hoje/amanhã)
    projeto_pendentes = base_qs.filter(
        filtro,
        projeto__isnull=False,
        prazo__gte=fim_amanha,
    ).order_by('prazo')

    total_projeto = len(atrasadas_projeto) + len(urgencias_hoje_projeto) + len(vencendo_amanha_projeto) + projeto_pendentes.count()

    # Contas a pagar do dia (data_execucao == hoje e não pagas nem dispensadas)
    from financeiro.models import ContaPagarItem
    contas_pagar_hoje = ContaPagarItem.objects.filter(
        data_execucao=hoje, pago=False, dispensado=False,
        conta_pagar__empresa__in=empresas_filtro,
    ).select_related('conta_pagar', 'conta_pagar__empresa').order_by('data_vencimento')

    # Contas a pagar atrasadas (data_execucao < hoje e não pagas nem dispensadas)
    contas_pagar_atrasadas = ContaPagarItem.objects.filter(
        data_execucao__lt=hoje, pago=False, dispensado=False,
        conta_pagar__empresa__in=empresas_filtro,
    ).select_related('conta_pagar', 'conta_pagar__empresa').order_by('data_vencimento')

    context = {
        'pessoa': pessoa,
        'items': items,
        'tarefas_ativas': tarefas_ativas,
        'tarefas_em_andamento': tarefas_em_andamento,
        'tarefas_concluidas': tarefas_concluidas,
        'tarefas_standby': tarefas_standby,
        'hoje': hoje,
        'status_choices': StatusItem.choices,
        'status_filter': status_filter,
        'progresso': progresso,
        'total': total,
        'concluidas': concluidas,
        'em_standby': em_standby,
        # Demandas normais (sem projeto)
        'urgencias_hoje': urgencias_hoje_normal,
        'atrasadas': atrasadas,
        'vencendo_amanha': vencendo_amanha,
        # Demandas de projeto (aba Projetos)
        'atrasadas_projeto': atrasadas_projeto,
        'urgencias_hoje_projeto': urgencias_hoje_projeto,
        'vencendo_amanha_projeto': vencendo_amanha_projeto,
        'projeto_pendentes': projeto_pendentes,
        'total_projeto': total_projeto,
        # Financeiro
        'contas_pagar_hoje': contas_pagar_hoje,
        'contas_pagar_atrasadas': contas_pagar_atrasadas,
        'tarefas_canceladas': tarefas_canceladas,
    }

    # Cancelamentos pendentes de aprovação (gestor)
    if pessoa.eh_gestor:
        empresas_ids = pessoa.empresas.values_list('id', flat=True)
        context['cancelamentos_pendentes'] = ChecklistItem.objects.filter(
            cancelamento_solicitado=True,
            template__empresa__in=empresas_ids,
        ).select_related('template', 'responsavel', 'template__empresa').order_by('-criado_em')

    return render(request, 'checklists/rotina_diaria.html', context)


@login_required
def minhas_tarefas(request):
    """Alias para rotina_diaria - mantém compatibilidade"""
    return rotina_diaria(request)


# ============================================
# DEMANDAS / PENDÊNCIAS
# ============================================

@login_required
def lista_demandas(request):
    """Lista de demandas/pendências"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    # Filtros
    empresa_filter = request.GET.get('empresa', '')
    status_filter = request.GET.get('status', '')
    dias_concluidos = int(request.GET.get('dias', 7))
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')

    if pessoa.eh_gestor:
        # Gestor vê todas das suas empresas
        empresas = get_empresas_filtradas(pessoa, request)
        demandas_base = Demanda.objects.filter(empresa__in=empresas)
    else:
        # Funcionário vê apenas as dele
        demandas_base = Demanda.objects.filter(responsavel=pessoa)

    # Demandas pendentes (excluir concluídos)
    demandas = demandas_base.exclude(status='concluido')

    if empresa_filter:
        demandas = demandas.filter(empresa_id=empresa_filter)
    if status_filter:
        demandas = demandas.filter(status=status_filter)

    demandas = demandas.select_related('empresa', 'responsavel', 'solicitante')

    # Demandas concluídas (para a aba de concluídos)
    demandas_concluidas = demandas_base.filter(status='concluido')

    # Filtro por datas customizadas tem prioridade
    if data_inicio or data_fim:
        if data_inicio:
            demandas_concluidas = demandas_concluidas.filter(concluido_em__date__gte=data_inicio)
        if data_fim:
            demandas_concluidas = demandas_concluidas.filter(concluido_em__date__lte=data_fim)
    elif dias_concluidos > 0:
        # Filtro por dias (7, 30, etc)
        periodo = timezone.now() - timedelta(days=dias_concluidos)
        demandas_concluidas = demandas_concluidas.filter(concluido_em__gte=periodo)

    demandas_concluidas = demandas_concluidas.select_related(
        'empresa', 'responsavel', 'solicitante'
    ).order_by('-concluido_em')

    # Agrupar por empresa
    demandas_por_empresa = {}
    for demanda in demandas:
        empresa_nome = demanda.empresa.nome
        if empresa_nome not in demandas_por_empresa:
            demandas_por_empresa[empresa_nome] = {
                'empresa': demanda.empresa,
                'demandas': []
            }
        demandas_por_empresa[empresa_nome]['demandas'].append(demanda)

    # Projetos com demandas pendentes
    empresas_ids = get_empresas_filtradas(pessoa, request).values_list('id', flat=True)
    projetos = Projeto.objects.filter(
        empresa_id__in=empresas_ids,
        status__in=['planejamento', 'em_andamento'],
    ).select_related('empresa').order_by('empresa__nome', 'titulo')

    projetos_dados = []
    for proj in projetos:
        if pessoa.eh_gestor:
            demandas_proj = Demanda.objects.filter(projeto=proj).exclude(status='concluido')
        else:
            demandas_proj = Demanda.objects.filter(projeto=proj, responsavel=pessoa).exclude(status='concluido')
        if demandas_proj.exists():
            projetos_dados.append({
                'projeto': proj,
                'demandas': demandas_proj.select_related('responsavel'),
                'total': demandas_proj.count(),
                'atrasadas': demandas_proj.filter(prazo__lt=timezone.now()).count(),
            })
    total_projetos = sum(p['total'] for p in projetos_dados)

    # Pagamentos (contas a pagar) - apenas gestores
    pagamentos_vencidos = []
    pagamentos_a_vencer = []
    total_pagamentos = 0
    if pessoa.eh_gestor:
        from financeiro.models import ContaPagarItem
        hoje = timezone.localdate()
        empresas_pag = get_empresas_filtradas(pessoa, request)
        if empresa_filter:
            empresas_pag = empresas_pag.filter(id=empresa_filter)
        pagamentos_vencidos = ContaPagarItem.objects.filter(
            data_vencimento__lt=hoje, pago=False, dispensado=False,
            conta_pagar__empresa__in=empresas_pag,
        ).select_related('conta_pagar', 'conta_pagar__empresa').order_by('data_vencimento')
        pagamentos_a_vencer = ContaPagarItem.objects.filter(
            data_vencimento__gte=hoje, pago=False, dispensado=False,
            conta_pagar__empresa__in=empresas_pag,
        ).select_related('conta_pagar', 'conta_pagar__empresa').order_by('data_vencimento')
        total_pagamentos = pagamentos_vencidos.count() + pagamentos_a_vencer.count()

    context = {
        'pessoa': pessoa,
        'demandas_por_empresa': demandas_por_empresa,
        'empresas': pessoa.empresas.all(),
        'status_choices': StatusDemanda.choices,
        'empresa_filter': empresa_filter,
        'status_filter': status_filter,
        'total_demandas': demandas.count(),
        'demandas_concluidas': demandas_concluidas,
        'total_concluidas': demandas_concluidas.count(),
        'dias_concluidos': dias_concluidos,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'projetos_dados': projetos_dados,
        'total_projetos': total_projetos,
        'pagamentos_vencidos': pagamentos_vencidos,
        'pagamentos_a_vencer': pagamentos_a_vencer,
        'total_pagamentos': total_pagamentos,
    }
    return render(request, 'checklists/lista_demandas.html', context)


@login_required
def criar_demanda(request):
    """Cria uma nova demanda (gestores ou funcionários para si mesmos)"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('lista_demandas')

    if request.method == 'POST':
        empresa_id = request.POST.get('empresa')
        # Funcionário só pode criar pra si mesmo
        responsavel_id = request.POST.get('responsavel') if pessoa.eh_gestor else str(pessoa.id)
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao', '')
        instrucoes = request.POST.get('instrucoes', '')
        prazo = request.POST.get('prazo')
        prioridade = request.POST.get('prioridade', PrioridadeDemanda.MEDIA)
        tempo_estimado = int(request.POST.get('tempo_estimado', 0) or 0)
        projeto_id = request.POST.get('projeto') or None

        if not all([empresa_id, responsavel_id, titulo, prazo]):
            messages.error(request, 'Preencha todos os campos obrigatórios.')
        else:
            demanda = Demanda.objects.create(
                empresa_id=empresa_id,
                projeto_id=projeto_id,
                solicitante=pessoa,
                responsavel_id=responsavel_id,
                titulo=titulo,
                descricao=descricao,
                instrucoes=instrucoes,
                prazo=prazo,
                prioridade=prioridade,
                tempo_estimado=tempo_estimado,
            )

            # Criar subtarefas do checklist
            checklist_items = request.POST.get('checklist_items', '')
            for i, linha in enumerate(checklist_items.strip().split('\n')):
                linha = linha.strip()
                if linha:
                    SubTarefaDemanda.objects.create(
                        demanda=demanda,
                        titulo=linha,
                        ordem=i,
                    )

            # Upload de anexos
            for arquivo in request.FILES.getlist('anexos'):
                AnexoDemanda.objects.create(
                    demanda=demanda,
                    arquivo=arquivo,
                    nome_original=arquivo.name,
                    tamanho=arquivo.size,
                    enviado_por=pessoa,
                )

            messages.success(request, f'Demanda "{titulo}" criada com sucesso!')
            return redirect('detalhe_demanda', demanda_id=demanda.id)

    # Listar pessoas disponíveis
    empresas = get_empresas_filtradas(pessoa, request)
    if pessoa.eh_gestor:
        pessoas = Pessoa.objects.filter(empresas__in=empresas, ativo=True).distinct()
    else:
        pessoas = Pessoa.objects.filter(id=pessoa.id)

    projetos = Projeto.objects.filter(
        empresa__in=empresas
    ).exclude(status__in=[StatusProjeto.CONCLUIDO, StatusProjeto.CANCELADO]).select_related('empresa')

    # Pre-selecionar responsável se passado via GET
    responsavel_preselect = request.GET.get('responsavel')
    empresa_preselect = None
    if responsavel_preselect:
        responsavel_obj = Pessoa.objects.filter(id=responsavel_preselect).first()
        if responsavel_obj:
            # Pre-selecionar a primeira empresa em comum
            empresa_preselect = responsavel_obj.empresas.filter(id__in=empresas).first()

    context = {
        'pessoa': pessoa,
        'empresas': empresas,
        'pessoas': pessoas,
        'prioridades': PrioridadeDemanda.choices,
        'tempos_estimados': Demanda.TEMPO_ESTIMADO_CHOICES,
        'projetos': projetos,
        'responsavel_preselect': responsavel_preselect,
        'empresa_preselect': empresa_preselect,
    }
    return render(request, 'checklists/criar_demanda.html', context)


@login_required
def detalhe_demanda(request, demanda_id):
    """Detalhe de uma demanda"""
    demanda = get_object_or_404(Demanda, id=demanda_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa:
        return redirect('dashboard')

    # Verificar permissão
    if demanda.responsavel != pessoa and demanda.solicitante != pessoa and not pessoa.eh_gestor:
        messages.error(request, 'Você não tem permissão para ver esta demanda.')
        return redirect('lista_demandas')

    context = {
        'demanda': demanda,
        'pessoa': pessoa,
        'status_choices': StatusDemanda.choices,
        'prioridades': PrioridadeDemanda.choices,
    }
    return render(request, 'checklists/detalhe_demanda.html', context)


@login_required
def editar_demanda(request, demanda_id):
    """Edita uma demanda existente (gestor ou solicitante)"""
    demanda = get_object_or_404(Demanda, id=demanda_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (demanda.solicitante != pessoa and not pessoa.eh_gestor):
        messages.error(request, 'Sem permissão para editar.')
        return redirect('detalhe_demanda', demanda_id=demanda.id)

    if request.method == 'POST':
        demanda.titulo = request.POST.get('titulo', demanda.titulo)
        demanda.descricao = request.POST.get('descricao', '')
        demanda.instrucoes = request.POST.get('instrucoes', '')
        demanda.prazo = request.POST.get('prazo', demanda.prazo)
        demanda.prioridade = request.POST.get('prioridade', demanda.prioridade)
        tempo_estimado = request.POST.get('tempo_estimado')
        if tempo_estimado is not None:
            demanda.tempo_estimado = int(tempo_estimado or 0)
        responsavel_id = request.POST.get('responsavel')
        if responsavel_id:
            demanda.responsavel_id = responsavel_id
        projeto_id = request.POST.get('projeto')
        demanda.projeto_id = projeto_id or None
        demanda.save()
        messages.success(request, 'Demanda atualizada!')
        return redirect('detalhe_demanda', demanda_id=demanda.id)

    empresas = get_empresas_filtradas(pessoa, request)
    pessoas = Pessoa.objects.filter(empresas__in=empresas, ativo=True).distinct()
    projetos = Projeto.objects.filter(
        empresa__in=empresas
    ).exclude(status__in=['concluido', 'cancelado']).select_related('empresa')

    context = {
        'demanda': demanda,
        'pessoa': pessoa,
        'pessoas': pessoas,
        'prioridades': PrioridadeDemanda.choices,
        'tempos_estimados': Demanda.TEMPO_ESTIMADO_CHOICES,
        'projetos': projetos,
    }
    return render(request, 'checklists/editar_demanda.html', context)


@login_required
@require_POST
def mudar_status_demanda(request, demanda_id):
    """Muda o status de uma demanda"""
    demanda = get_object_or_404(Demanda, id=demanda_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa:
        return JsonResponse({'error': 'Usuário não vinculado'}, status=403)

    if demanda.responsavel != pessoa and not pessoa.eh_gestor:
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    novo_status = data.get('status')

    if novo_status not in [s[0] for s in StatusDemanda.choices]:
        return JsonResponse({'error': 'Status inválido'}, status=400)

    if novo_status == StatusDemanda.CONCLUIDO:
        demanda.marcar_concluido()
    else:
        demanda.status = novo_status
        if novo_status == StatusDemanda.EM_ANDAMENTO:
            # Iniciar timer ao mudar para Em Andamento
            if not demanda.timer_ativo:
                demanda.iniciar_timer()
        if novo_status != StatusDemanda.DEPENDENTE:
            demanda.dependencia_resolvida_em = timezone.now() if demanda.dependente_de else None
        demanda.save()

    return JsonResponse({
        'status': 'ok',
        'novo_status': demanda.status,
        'status_display': demanda.get_status_display()
    })


@login_required
@require_POST
def reabrir_demanda(request, demanda_id):
    """Reabre uma demanda concluída"""
    demanda = get_object_or_404(Demanda, id=demanda_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (demanda.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    demanda.reabrir()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def timer_demanda_iniciar(request, demanda_id):
    """Inicia o timer de uma demanda"""
    demanda = get_object_or_404(Demanda, id=demanda_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (demanda.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    demanda.iniciar_timer()
    # Iniciar timer → muda para Em Andamento
    if demanda.status not in (StatusDemanda.EM_ANDAMENTO, StatusDemanda.CONCLUIDO):
        demanda.status = StatusDemanda.EM_ANDAMENTO
        demanda.save()
    return JsonResponse({
        'status': 'ok',
        'timer_ativo': demanda.timer_ativo,
        'tempo_total': demanda.get_tempo_total(),
        'tempo_formatado': demanda.get_tempo_formatado(),
        'demanda_status': demanda.status,
    })


@login_required
@require_POST
def timer_demanda_pausar(request, demanda_id):
    """Pausa o timer de uma demanda"""
    demanda = get_object_or_404(Demanda, id=demanda_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (demanda.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    demanda.pausar_timer()
    # Apenas pausa o timer, mantém o status atual
    return JsonResponse({
        'status': 'ok',
        'timer_ativo': demanda.timer_ativo,
        'tempo_total': demanda.get_tempo_total(),
        'tempo_formatado': demanda.get_tempo_formatado(),
        'demanda_status': demanda.status,
    })


@login_required
@require_POST
def timer_demanda_editar(request, demanda_id):
    """Permite ao gestor editar/zerar o timer de uma demanda"""
    demanda = get_object_or_404(Demanda, id=demanda_id)
    pessoa = get_pessoa_or_redirect(request)

    # Apenas gestores podem editar o timer
    if not pessoa or not pessoa.eh_gestor:
        return JsonResponse({'error': 'Apenas gestores podem editar o timer'}, status=403)

    data = json.loads(request.body)

    # Parar o timer se estiver ativo
    if demanda.timer_ativo:
        demanda.timer_ativo = False
        demanda.timer_inicio = None

    # Atualizar tempo acumulado
    novo_tempo = data.get('tempo_segundos', 0)
    demanda.timer_acumulado = max(0, int(novo_tempo))
    demanda.save()

    return JsonResponse({
        'status': 'ok',
        'timer_ativo': demanda.timer_ativo,
        'tempo_total': demanda.get_tempo_total(),
        'tempo_formatado': demanda.get_tempo_formatado(),
    })


@login_required
@require_POST
def timer_tarefa_editar(request, item_id):
    """Permite ao admin editar/zerar o timer de uma tarefa (checklist)"""
    item = get_object_or_404(ChecklistItem, id=item_id)

    # Apenas superusers (admin) podem editar o timer
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Apenas administradores podem editar o timer'}, status=403)

    data = json.loads(request.body)

    # Parar o timer se estiver ativo
    if item.timer_ativo:
        item.timer_ativo = False
        item.timer_inicio = None

    # Atualizar tempo acumulado
    novo_tempo = data.get('tempo_segundos', 0)
    item.timer_acumulado = max(0, int(novo_tempo))
    item.save()

    return JsonResponse({
        'status': 'ok',
        'timer_ativo': item.timer_ativo,
        'tempo_total': item.get_tempo_total(),
        'tempo_formatado': item.get_tempo_formatado(),
    })


@login_required
@require_POST
def salvar_anotacao_demanda(request, demanda_id):
    """Salva anotações da demanda"""
    demanda = get_object_or_404(Demanda, id=demanda_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (demanda.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    demanda.anotacoes = data.get('anotacoes', '')
    demanda.save()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def adicionar_comentario_demanda(request, demanda_id):
    """Adiciona um comentário à demanda"""
    demanda = get_object_or_404(Demanda, id=demanda_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa:
        return JsonResponse({'error': 'Usuário não vinculado'}, status=403)

    data = json.loads(request.body)
    texto = data.get('texto', '').strip()

    if not texto:
        return JsonResponse({'error': 'Texto obrigatório'}, status=400)

    comentario = ComentarioDemanda.objects.create(
        demanda=demanda,
        autor=pessoa,
        texto=texto
    )

    return JsonResponse({
        'status': 'ok',
        'comentario': {
            'id': comentario.id,
            'autor': comentario.autor.nome,
            'texto': comentario.texto,
            'criado_em': comentario.criado_em.strftime('%d/%m/%Y %H:%M'),
        }
    })


@login_required
@require_POST
def upload_anexo_demanda(request, demanda_id):
    """Upload de anexo para demanda"""
    demanda = get_object_or_404(Demanda, id=demanda_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa:
        return JsonResponse({'error': 'Usuário não vinculado'}, status=403)

    arquivo = request.FILES.get('arquivo')
    if not arquivo:
        return JsonResponse({'error': 'Arquivo não enviado'}, status=400)

    anexo = AnexoDemanda.objects.create(
        demanda=demanda,
        arquivo=arquivo,
        nome_original=arquivo.name,
        tamanho=arquivo.size,
        enviado_por=pessoa,
    )

    return JsonResponse({
        'status': 'ok',
        'anexo': {
            'id': anexo.id,
            'nome': anexo.nome_original,
            'tamanho': anexo.get_tamanho_formatado(),
            'url': anexo.arquivo.url,
        }
    })


@login_required
@require_POST
def excluir_anexo_demanda(request, anexo_id):
    """Exclui um anexo"""
    anexo = get_object_or_404(AnexoDemanda, id=anexo_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (anexo.enviado_por != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    anexo.arquivo.delete()
    anexo.delete()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def adicionar_subtarefa_demanda(request, demanda_id):
    """Adiciona subtarefa à demanda"""
    demanda = get_object_or_404(Demanda, id=demanda_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (demanda.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    titulo = data.get('titulo', '').strip()

    if not titulo:
        return JsonResponse({'error': 'Título obrigatório'}, status=400)

    ultima_ordem = demanda.subtarefas_demanda.order_by('-ordem').first()
    ordem = (ultima_ordem.ordem + 1) if ultima_ordem else 0

    subtarefa = SubTarefaDemanda.objects.create(
        demanda=demanda,
        titulo=titulo,
        ordem=ordem
    )

    return JsonResponse({
        'status': 'ok',
        'subtarefa': {
            'id': subtarefa.id,
            'titulo': subtarefa.titulo,
            'concluida': subtarefa.concluida,
        },
        'progresso': demanda.get_progresso()
    })


@login_required
@require_POST
def toggle_subtarefa_demanda(request, subtarefa_id):
    """Toggle subtarefa de demanda"""
    subtarefa = get_object_or_404(SubTarefaDemanda, id=subtarefa_id)
    demanda = subtarefa.demanda
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (demanda.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    subtarefa.concluida = not subtarefa.concluida
    subtarefa.save()

    return JsonResponse({
        'status': 'ok',
        'concluida': subtarefa.concluida,
        'progresso': demanda.get_progresso()
    })


@login_required
@require_POST
def excluir_subtarefa_demanda(request, subtarefa_id):
    """Exclui subtarefa de demanda"""
    subtarefa = get_object_or_404(SubTarefaDemanda, id=subtarefa_id)
    demanda = subtarefa.demanda
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (demanda.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    subtarefa.delete()
    return JsonResponse({
        'status': 'ok',
        'progresso': demanda.get_progresso()
    })


@login_required
@require_POST
def reordenar_subtarefas_demanda(request, demanda_id):
    """Reordena subtarefas de uma demanda via drag & drop"""
    demanda = get_object_or_404(Demanda, id=demanda_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (demanda.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    for item in data.get('items', []):
        SubTarefaDemanda.objects.filter(id=item['id'], demanda=demanda).update(ordem=item['ordem'])

    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def marcar_dependente_demanda(request, demanda_id):
    """Marca demanda como dependente"""
    demanda = get_object_or_404(Demanda, id=demanda_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (demanda.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    dependente_id = data.get('dependente_id')
    dependente_externo = data.get('dependente_externo', '')
    telefone_externo = data.get('telefone_externo', '')
    motivo = data.get('motivo', '')

    if dependente_id:
        dependente = get_object_or_404(Pessoa, id=dependente_id)
        demanda.dependente_de = dependente
        demanda.dependente_externo = ''
        demanda.telefone_dependente_externo = ''
        demanda.motivo_dependencia = motivo
        demanda.status = StatusDemanda.DEPENDENTE
        demanda.dependencia_resolvida_em = None
    elif dependente_externo:
        demanda.dependente_de = None
        demanda.dependente_externo = dependente_externo
        demanda.telefone_dependente_externo = telefone_externo
        demanda.motivo_dependencia = motivo
        demanda.status = StatusDemanda.DEPENDENTE
        demanda.dependencia_resolvida_em = None
        # Salvar/atualizar pessoa externa para reutilização
        from core.models import PessoaExterna
        pe, _ = PessoaExterna.objects.get_or_create(
            nome__iexact=dependente_externo,
            defaults={'nome': dependente_externo, 'telefone': telefone_externo}
        )
        if telefone_externo and not pe.telefone:
            pe.telefone = telefone_externo
            pe.save()
    else:
        demanda.dependente_de = None
        demanda.dependente_externo = ''
        demanda.telefone_dependente_externo = ''
        demanda.motivo_dependencia = ''
        demanda.dependencia_resolvida_em = timezone.now()
        if demanda.status == StatusDemanda.DEPENDENTE:
            demanda.status = StatusDemanda.EM_ANDAMENTO

    demanda.save()

    nome = demanda.dependente_de.nome if demanda.dependente_de else (demanda.dependente_externo or None)
    return JsonResponse({
        'status': 'ok',
        'demanda_status': demanda.status,
        'dependente_nome': nome
    })


# ============================================
# ROTINA DIÁRIA (views existentes atualizadas)
# ============================================

@login_required
def marcar_concluido(request, item_id):
    """Marca um item como concluído"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Sem permissão'}, status=403)
        messages.error(request, 'Você não tem permissão para alterar esta tarefa.')
        return redirect('dashboard')

    if request.method == 'POST':
        observacoes = request.POST.get('observacoes', '')
        item.observacoes = observacoes
        item.marcar_concluido()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'message': f'Tarefa "{item.template.titulo}" concluída!'})

        messages.success(request, f'Tarefa "{item.template.titulo}" marcada como concluída!')

    return redirect('rotina_diaria')


@login_required
def marcar_em_andamento(request, item_id):
    """Marca um item como em andamento"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        messages.error(request, 'Você não tem permissão para alterar esta tarefa.')
        return redirect('dashboard')

    if item.status != StatusItem.EM_ANDAMENTO:
        item.status = StatusItem.EM_ANDAMENTO
        item.save()
        # Iniciar timer automaticamente
        if not item.timer_ativo:
            item.iniciar_timer()
        messages.info(request, f'Tarefa "{item.template.titulo}" iniciada!')

    return redirect('rotina_diaria')


@login_required
def ver_processo(request, template_id):
    """Visualiza o processo/instruções de uma tarefa"""
    template = get_object_or_404(ChecklistTemplate, id=template_id)
    return render(request, 'checklists/ver_processo.html', {'template': template})


@login_required
def relatorio_workspace(request, workspace_id):
    """Relatório do workspace (apenas gestores)"""
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or not pessoa.eh_gestor:
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')

    empresa = get_object_or_404(Empresa, id=workspace_id)
    hoje = timezone.localdate()

    if empresa not in pessoa.empresas.all():
        messages.error(request, 'Você não tem acesso a esta empresa.')
        return redirect('dashboard')

    # Estatísticas por pessoa
    pessoas_stats = []
    for p in empresa.pessoas.filter(ativo=True):
        items = ChecklistItem.objects.filter(
            responsavel=p,
            data_referencia=hoje,
            template__empresa=empresa
        )
        demandas = Demanda.objects.filter(
            responsavel=p,
            empresa=empresa
        ).exclude(status=StatusDemanda.CONCLUIDO)

        pessoas_stats.append({
            'pessoa': p,
            'total': items.count(),
            'concluidos': items.filter(status=StatusItem.CONCLUIDO).count(),
            'pendentes': items.filter(status__in=[StatusItem.PENDENTE, StatusItem.EM_ANDAMENTO]).count(),
            'atrasados': items.filter(status=StatusItem.ATRASADO).count(),
            'demandas_pendentes': demandas.count(),
        })

    context = {
        'empresa': empresa,
        'workspace': empresa,  # Alias para compatibilidade
        'pessoas_stats': pessoas_stats,
        'hoje': hoje,
    }
    return render(request, 'checklists/relatorio_workspace.html', context)


@login_required
@require_POST
def timer_iniciar(request, item_id):
    """Inicia o timer de uma tarefa"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    item.iniciar_timer()
    # Iniciar timer → muda para Em Andamento
    if item.status not in (StatusItem.EM_ANDAMENTO, StatusItem.CONCLUIDO):
        item.status = StatusItem.EM_ANDAMENTO
        item.save()
    return JsonResponse({
        'status': 'ok',
        'timer_ativo': item.timer_ativo,
        'tempo_total': item.get_tempo_total(),
        'tempo_formatado': item.get_tempo_formatado(),
        'item_status': item.status,
    })


@login_required
@require_POST
def timer_pausar(request, item_id):
    """Pausa o timer de uma tarefa"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    item.pausar_timer()
    # Apenas pausa o timer, mantém o status atual
    return JsonResponse({
        'status': 'ok',
        'timer_ativo': item.timer_ativo,
        'tempo_total': item.get_tempo_total(),
        'tempo_formatado': item.get_tempo_formatado(),
        'item_status': item.status,
    })


@login_required
def timer_status(request, item_id):
    """Retorna o status atual do timer"""
    item = get_object_or_404(ChecklistItem, id=item_id)

    return JsonResponse({
        'timer_ativo': item.timer_ativo,
        'tempo_total': item.get_tempo_total(),
        'tempo_formatado': item.get_tempo_formatado(),
        'timer_inicio': item.timer_inicio.isoformat() if item.timer_inicio else None,
        'item_status': item.status,
    })


@login_required
def detalhe_tarefa(request, item_id):
    """Página de detalhe da tarefa com timer e anotações"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        messages.error(request, 'Você não tem permissão para ver esta tarefa.')
        return redirect('dashboard')

    context = {
        'item': item,
        'pessoa': pessoa,
    }
    return render(request, 'checklists/detalhe_tarefa.html', context)


@login_required
@require_POST
def salvar_anotacao(request, item_id):
    """Salva as anotações da tarefa"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    item.anotacoes = data.get('anotacoes', '')
    item.save()

    return JsonResponse({'status': 'ok', 'message': 'Anotação salva'})


@login_required
@require_POST
def adicionar_subtarefa(request, item_id):
    """Adiciona uma subtarefa ao item"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    titulo = data.get('titulo', '').strip()

    if not titulo:
        return JsonResponse({'error': 'Título obrigatório'}, status=400)

    ultima_ordem = item.subtarefas.order_by('-ordem').first()
    ordem = (ultima_ordem.ordem + 1) if ultima_ordem else 0

    subtarefa = SubTarefa.objects.create(
        checklist_item=item,
        titulo=titulo,
        ordem=ordem
    )

    return JsonResponse({
        'status': 'ok',
        'subtarefa': {
            'id': subtarefa.id,
            'titulo': subtarefa.titulo,
            'concluida': subtarefa.concluida,
        },
        'progresso': item.get_progresso()
    })


@login_required
@require_POST
def toggle_subtarefa(request, subtarefa_id):
    """Marca/desmarca uma subtarefa como concluída"""
    subtarefa = get_object_or_404(SubTarefa, id=subtarefa_id)
    item = subtarefa.checklist_item
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    subtarefa.concluida = not subtarefa.concluida
    subtarefa.save()

    return JsonResponse({
        'status': 'ok',
        'concluida': subtarefa.concluida,
        'progresso': item.get_progresso()
    })


@login_required
@require_POST
def excluir_subtarefa(request, subtarefa_id):
    """Exclui uma subtarefa"""
    subtarefa = get_object_or_404(SubTarefa, id=subtarefa_id)
    item = subtarefa.checklist_item
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    subtarefa.delete()

    return JsonResponse({
        'status': 'ok',
        'progresso': item.get_progresso()
    })


@login_required
@require_POST
def reordenar_subtarefas(request, item_id):
    """Reordena subtarefas de um checklist item via drag & drop"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    for sub in data.get('items', []):
        SubTarefa.objects.filter(id=sub['id'], checklist_item=item).update(ordem=sub['ordem'])

    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def sincronizar_subtarefas(request, item_id):
    """Sincroniza subtarefas do template para o item"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    # Buscar subtarefas do template que não existem no item
    subtarefas_template = item.template.subtarefas_template.all()
    titulos_existentes = set(item.subtarefas.values_list('titulo', flat=True))

    adicionadas = 0
    for st in subtarefas_template:
        if st.titulo not in titulos_existentes:
            SubTarefa.objects.create(
                checklist_item=item,
                titulo=st.titulo,
                ordem=st.ordem,
            )
            adicionadas += 1

    return JsonResponse({
        'status': 'ok',
        'adicionadas': adicionadas,
        'progresso': item.get_progresso()
    })


@login_required
@require_POST
def cancelar_tarefa(request, item_id):
    """Cancela uma tarefa da rotina - gestor cancela direto, funcionário solicita"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    motivo = request.POST.get('motivo', '')

    if pessoa.eh_gestor:
        # Gestor cancela direto
        item.pausar_timer()
        item.status = StatusItem.CANCELADO
        item.cancelamento_motivo = motivo
        item.save()
    else:
        # Funcionário solicita cancelamento
        if item.responsavel != pessoa:
            return JsonResponse({'error': 'Sem permissão'}, status=403)
        item.cancelamento_solicitado = True
        item.cancelamento_motivo = motivo
        item.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
    return redirect('rotina_diaria')


@login_required
@require_POST
def aprovar_cancelamento(request, item_id):
    """Gestor aprova solicitação de cancelamento"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    item.pausar_timer()
    item.status = StatusItem.CANCELADO
    item.cancelamento_solicitado = False
    item.save()
    return redirect('rotina_diaria')


@login_required
@require_POST
def recusar_cancelamento(request, item_id):
    """Gestor recusa solicitação de cancelamento"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    item.cancelamento_solicitado = False
    item.cancelamento_motivo = ''
    item.save()
    return redirect('rotina_diaria')


@login_required
@require_POST
def mudar_status(request, item_id):
    """Muda o status de uma tarefa"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    novo_status = data.get('status')

    if novo_status not in [s[0] for s in StatusItem.choices]:
        return JsonResponse({'error': 'Status inválido'}, status=400)

    if novo_status == StatusItem.CONCLUIDO:
        item.marcar_concluido()
    else:
        item.status = novo_status
        if novo_status != StatusItem.DEPENDENTE:
            item.dependencia_resolvida_em = timezone.now() if item.dependente_de else None
        item.save()

    return JsonResponse({
        'status': 'ok',
        'novo_status': item.status,
        'status_display': item.get_status_display()
    })


@login_required
@require_POST
def marcar_dependente(request, item_id):
    """Marca uma tarefa como dependente de outra pessoa"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    dependente_id = data.get('dependente_id')
    dependente_externo = data.get('dependente_externo', '')
    telefone_externo = data.get('telefone_externo', '')
    motivo = data.get('motivo', '')

    if dependente_id:
        dependente = get_object_or_404(Pessoa, id=dependente_id)
        item.dependente_de = dependente
        item.dependente_externo = ''
        item.telefone_dependente_externo = ''
        item.motivo_dependencia = motivo
        item.status = StatusItem.DEPENDENTE
        item.dependencia_resolvida_em = None
    elif dependente_externo:
        item.dependente_de = None
        item.dependente_externo = dependente_externo
        item.telefone_dependente_externo = telefone_externo
        item.motivo_dependencia = motivo
        item.status = StatusItem.DEPENDENTE
        item.dependencia_resolvida_em = None
        from core.models import PessoaExterna
        pe, _ = PessoaExterna.objects.get_or_create(
            nome__iexact=dependente_externo,
            defaults={'nome': dependente_externo, 'telefone': telefone_externo}
        )
        if telefone_externo and not pe.telefone:
            pe.telefone = telefone_externo
            pe.save()
    else:
        item.dependente_de = None
        item.dependente_externo = ''
        item.telefone_dependente_externo = ''
        item.motivo_dependencia = ''
        item.dependencia_resolvida_em = timezone.now()
        if item.status == StatusItem.DEPENDENTE:
            item.status = StatusItem.EM_ANDAMENTO

    item.save()

    nome = item.dependente_de.nome if item.dependente_de else (item.dependente_externo or None)
    return JsonResponse({
        'status': 'ok',
        'item_status': item.status,
        'dependente_nome': nome
    })


@login_required
@require_POST
def pausar_tarefa(request, item_id):
    """Pausa uma tarefa (coloca em standby sem dependência)"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    motivo = data.get('motivo', 'Pausado manualmente')

    # Pausar o timer se estiver rodando
    if item.timer_ativo:
        item.pausar_timer()

    # Marcar como dependente (standby) com motivo
    item.dependente_de = None  # Sem pessoa específica
    item.motivo_dependencia = motivo
    item.status = StatusItem.DEPENDENTE
    item.save()

    return JsonResponse({
        'status': 'ok',
        'item_status': item.status,
        'motivo': motivo
    })


@login_required
@require_POST
def despausar_tarefa(request, item_id):
    """Retira tarefa do standby e volta para em andamento"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    item.dependente_de = None
    item.motivo_dependencia = ''
    item.dependencia_resolvida_em = timezone.now()
    item.status = StatusItem.EM_ANDAMENTO
    item.save()

    return JsonResponse({
        'status': 'ok',
        'item_status': item.status
    })


@login_required
def listar_pessoas(request):
    """Retorna lista de pessoas para seleção de dependente"""
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa:
        return JsonResponse({'pessoas': []})

    # Retorna pessoas das mesmas empresas
    pessoas = Pessoa.objects.filter(
        empresas__in=get_empresas_filtradas(pessoa, request),
        ativo=True
    ).distinct().exclude(id=pessoa.id)

    return JsonResponse({
        'pessoas': [
            {'id': p.id, 'nome': p.nome, 'cargo': p.cargo.nome if p.cargo else ''}
            for p in pessoas
        ]
    })


@login_required
def listar_pessoas_empresa(request, empresa_id):
    """Retorna pessoas de uma empresa específica (apenas se o usuário tem acesso)"""
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa:
        return JsonResponse({'pessoas': []})

    # Garante isolamento: só retorna pessoas de empresas que o user tem acesso
    empresas_user = pessoa.empresas.values_list('id', flat=True)
    if int(empresa_id) not in empresas_user:
        return JsonResponse({'pessoas': []})

    pessoas = Pessoa.objects.filter(
        empresas__id=empresa_id,
        ativo=True
    ).distinct().order_by('nome')

    return JsonResponse({
        'pessoas': [
            {'id': p.id, 'nome': p.nome, 'cargo': p.cargo.nome if p.cargo else ''}
            for p in pessoas
        ]
    })


@login_required
def listar_clientes_empresa(request, empresa_id):
    """Retorna clientes de uma empresa específica (apenas se o usuário tem acesso)"""
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa:
        return JsonResponse({'clientes': []})

    empresas_user = pessoa.empresas.values_list('id', flat=True)
    if int(empresa_id) not in empresas_user:
        return JsonResponse({'clientes': []})

    clientes = Cliente.objects.filter(
        empresa_id=empresa_id,
        ativo=True
    ).order_by('nome')

    return JsonResponse({
        'clientes': [
            {'id': c.id, 'nome': c.nome, 'tipo': c.tipo}
            for c in clientes
        ]
    })


@login_required
def buscar_pessoas_externas(request):
    """Busca pessoas externas por nome (autocomplete)"""
    q = request.GET.get('q', '').strip()
    if len(q) < 1:
        return JsonResponse({'pessoas': []})

    from core.models import PessoaExterna
    pessoas = PessoaExterna.objects.filter(nome__icontains=q)[:10]
    return JsonResponse({
        'pessoas': [
            {'id': p.id, 'nome': p.nome, 'telefone': p.telefone, 'empresa': p.empresa_nome}
            for p in pessoas
        ]
    })


# ============================================
# JUSTIFICATIVA E APROVEITAMENTO
# ============================================

from .models import AproveitamentoDiario, TarefaNaoConcluida
from datetime import datetime, timedelta
from django.db.models import Avg, Sum
from calendar import monthrange


@login_required
@require_POST
def salvar_justificativa(request, item_id):
    """Salva a justificativa de uma tarefa não concluída"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or (item.responsavel != pessoa and not pessoa.eh_gestor):
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    item.justificativa = data.get('justificativa', '')
    item.save()

    # Atualizar registro de tarefa não concluída se existir
    try:
        registro = item.registro_nao_concluida
        registro.justificativa = item.justificativa
        registro.save()
    except TarefaNaoConcluida.DoesNotExist:
        pass

    return JsonResponse({'status': 'ok'})


@login_required
def acompanhamento(request):
    """Tela de acompanhamento unificada - tempo real e histórico"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    if not pessoa.eh_gestor:
        messages.error(request, 'Acesso restrito a gestores.')
        return redirect('dashboard')

    hoje = timezone.localdate()
    agora = timezone.now()

    # Aba ativa (hoje ou historico)
    aba = request.GET.get('aba', 'hoje')

    # Filtro por empresa
    empresas = get_empresas_filtradas(pessoa, request)
    empresa_id = request.GET.get('empresa')
    empresa_selecionada = None
    if empresa_id:
        empresa_selecionada = empresas.filter(id=empresa_id).first()

    empresas_filtro = [empresa_selecionada] if empresa_selecionada else list(empresas)

    # Contexto base
    context = {
        'empresas': empresas,
        'empresa_selecionada': empresa_selecionada,
        'hoje': hoje,
        'aba': aba,
    }

    if aba == 'hoje':
        # ============================================
        # ABA TEMPO REAL
        # ============================================
        funcionarios = Pessoa.objects.filter(
            empresas__in=empresas_filtro,
            ativo=True
        ).distinct().order_by('nome')

        funcionarios_dados = []
        for func in funcionarios:
            tarefas = ChecklistItem.objects.filter(
                responsavel=func,
                data_referencia=hoje
            ).select_related('template', 'template__empresa').order_by('ordem', 'template__ordem_execucao')

            if empresa_selecionada:
                tarefas = tarefas.filter(template__empresa=empresa_selecionada)

            total = tarefas.count()
            concluidas = tarefas.filter(status=StatusItem.CONCLUIDO).count()
            em_andamento = tarefas.filter(status=StatusItem.EM_ANDAMENTO).count()
            pendentes = tarefas.filter(status=StatusItem.PENDENTE).count()
            atrasadas = tarefas.filter(status=StatusItem.ATRASADO).count()
            dependentes = tarefas.filter(status=StatusItem.DEPENDENTE).count()

            aproveitamento = int((concluidas / total) * 100) if total > 0 else 0

            tarefa_atual = tarefas.filter(
                Q(status=StatusItem.EM_ANDAMENTO) | Q(timer_ativo=True)
            ).first()

            tempo_total = sum(t.get_tempo_total() for t in tarefas)
            horas = tempo_total // 3600
            minutos = (tempo_total % 3600) // 60

            demandas = Demanda.objects.filter(
                responsavel=func
            ).exclude(status__in=[StatusDemanda.CONCLUIDO, StatusDemanda.CANCELADO])

            if empresa_selecionada:
                demandas = demandas.filter(empresa=empresa_selecionada)

            demandas_atrasadas = demandas.filter(prazo__lt=agora).count()

            funcionarios_dados.append({
                'pessoa': func,
                'tarefas': list(tarefas),
                'total': total,
                'concluidas': concluidas,
                'em_andamento': em_andamento,
                'pendentes': pendentes,
                'atrasadas': atrasadas,
                'dependentes': dependentes,
                'aproveitamento': aproveitamento,
                'tarefa_atual': tarefa_atual,
                'tempo_formatado': f"{horas}h {minutos}m",
                'demandas_abertas': demandas.count(),
                'demandas_atrasadas': demandas_atrasadas,
            })

        funcionarios_dados.sort(key=lambda x: (-1 if x['tarefa_atual'] else 0, -x['aproveitamento']))

        total_funcionarios = len(funcionarios_dados)
        total_tarefas = sum(f['total'] for f in funcionarios_dados)
        total_concluidas = sum(f['concluidas'] for f in funcionarios_dados)
        aproveitamento_medio = int((total_concluidas / total_tarefas) * 100) if total_tarefas > 0 else 0
        trabalhando_agora = sum(1 for f in funcionarios_dados if f['tarefa_atual'])

        context.update({
            'funcionarios': funcionarios_dados,
            'total_funcionarios': total_funcionarios,
            'total_tarefas': total_tarefas,
            'total_concluidas': total_concluidas,
            'aproveitamento_medio': aproveitamento_medio,
            'trabalhando_agora': trabalhando_agora,
        })

    else:
        # ============================================
        # ABA HISTÓRICO
        # ============================================
        mes = request.GET.get('mes')
        ano = request.GET.get('ano')

        if mes and ano:
            mes = int(mes)
            ano = int(ano)
        else:
            mes = hoje.month
            ano = hoje.year

        data_inicio = date(ano, mes, 1)
        ultimo_dia = monthrange(ano, mes)[1]
        data_fim = date(ano, mes, ultimo_dia)

        # Filtro por pessoa
        pessoa_id = request.GET.get('pessoa')
        ver_todos = pessoa_id == 'todos' or not pessoa_id

        pessoas_equipe = Pessoa.objects.filter(
            empresas__in=empresas_filtro,
            ativo=True
        ).distinct()

        if ver_todos:
            pessoa_selecionada = None
            aproveitamentos = AproveitamentoDiario.objects.filter(
                pessoa__in=pessoas_equipe,
                data__gte=data_inicio,
                data__lte=data_fim
            ).select_related('pessoa').order_by('-data')

            media_mes = aproveitamentos.aggregate(
                media=Avg('percentual'),
                tempo_total=Sum('tempo_total_segundos')
            )

            tarefas_nao_concluidas = ChecklistItem.objects.filter(
                responsavel__in=pessoas_equipe,
                data_referencia__gte=data_inicio,
                data_referencia__lte=data_fim
            ).exclude(
                status=StatusItem.CONCLUIDO
            ).select_related('template', 'template__empresa', 'responsavel').order_by('-data_referencia')[:50]

            # Gráfico: média de todos por dia
            dados_grafico = []
            for dia in range(1, ultimo_dia + 1):
                data_dia = date(ano, mes, dia)
                aprov_dia = aproveitamentos.filter(data=data_dia)
                agg = aprov_dia.aggregate(
                    media=Avg('percentual'),
                    concluidas=Sum('tarefas_concluidas'),
                    total=Sum('total_tarefas')
                )
                dados_grafico.append({
                    'dia': dia,
                    'data': data_dia,
                    'percentual': float(agg['media']) if agg['media'] else None,
                    'concluidas': agg['concluidas'] or 0,
                    'total': agg['total'] or 0,
                })
        else:
            pessoa_selecionada = get_object_or_404(Pessoa, id=pessoa_id)

            aproveitamentos = AproveitamentoDiario.objects.filter(
                pessoa=pessoa_selecionada,
                data__gte=data_inicio,
                data__lte=data_fim
            ).select_related('pessoa').order_by('-data')

            media_mes = aproveitamentos.aggregate(
                media=Avg('percentual'),
                tempo_total=Sum('tempo_total_segundos')
            )

            tarefas_nao_concluidas = ChecklistItem.objects.filter(
                responsavel=pessoa_selecionada,
                data_referencia__gte=data_inicio,
                data_referencia__lte=data_fim
            ).exclude(
                status=StatusItem.CONCLUIDO
            ).select_related('template', 'template__empresa', 'responsavel').order_by('-data_referencia')[:50]

            dados_grafico = []
            for dia in range(1, ultimo_dia + 1):
                data_dia = date(ano, mes, dia)
                aprov = aproveitamentos.filter(data=data_dia).first()
                dados_grafico.append({
                    'dia': dia,
                    'data': data_dia,
                    'percentual': float(aprov.percentual) if aprov else None,
                    'concluidas': aprov.tarefas_concluidas if aprov else 0,
                    'total': aprov.total_tarefas if aprov else 0,
                })

        # Lista de meses para filtro
        meses = [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
            (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
            (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ]

        # Total de dias com registro
        total_dias_registrados = aproveitamentos.values('data').distinct().count()

        context.update({
            'pessoas_lista': pessoas_equipe,
            'pessoa_selecionada': pessoa_selecionada,
            'ver_todos': ver_todos,
            'aproveitamentos': aproveitamentos,
            'tarefas_nao_concluidas': tarefas_nao_concluidas,
            'dados_grafico': dados_grafico,
            'media_mes': media_mes['media'] or 0,
            'tempo_total_mes': media_mes['tempo_total'] or 0,
            'total_dias_registrados': total_dias_registrados,
            'mes': mes,
            'ano': ano,
            'meses': meses,
            'anos': range(2024, hoje.year + 2),
        })

    return render(request, 'checklists/acompanhamento.html', context)


@login_required
def aproveitamento(request):
    """Tela de aproveitamento do funcionário"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    # Parâmetros de filtro
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')

    hoje = timezone.localdate()
    if mes and ano:
        mes = int(mes)
        ano = int(ano)
    else:
        mes = hoje.month
        ano = hoje.year

    # Data início e fim do mês
    data_inicio = datetime(ano, mes, 1).date()
    ultimo_dia = monthrange(ano, mes)[1]
    data_fim = datetime(ano, mes, ultimo_dia).date()

    # Se é gestor, pode ver de outros ou "todos"
    pessoa_id = request.GET.get('pessoa')
    ver_todos = pessoa.eh_gestor and pessoa_id == 'todos'

    if ver_todos:
        pessoa_visualizada = None
        pessoas_equipe = Pessoa.objects.filter(
            empresas__in=get_empresas_filtradas(pessoa, request), ativo=True
        ).distinct()

        aproveitamentos = AproveitamentoDiario.objects.filter(
            pessoa__in=pessoas_equipe,
            data__gte=data_inicio,
            data__lte=data_fim
        ).order_by('data')

        media_mes = aproveitamentos.aggregate(
            media=Avg('percentual'),
            tempo_total=Sum('tempo_total_segundos')
        )

        tarefas_nao_concluidas = ChecklistItem.objects.filter(
            responsavel__in=pessoas_equipe,
            data_referencia__gte=data_inicio,
            data_referencia__lte=data_fim
        ).exclude(
            status=StatusItem.CONCLUIDO
        ).select_related('template', 'template__empresa', 'responsavel').order_by('-data_referencia')

        # Gráfico: média de todos por dia
        dados_grafico = []
        for dia in range(1, ultimo_dia + 1):
            data_dia = datetime(ano, mes, dia).date()
            aprov_dia = aproveitamentos.filter(data=data_dia)
            agg = aprov_dia.aggregate(
                media=Avg('percentual'),
                concluidas=Sum('tarefas_concluidas'),
                total=Sum('total_tarefas')
            )
            dados_grafico.append({
                'dia': dia,
                'data': data_dia,
                'percentual': float(agg['media']) if agg['media'] else None,
                'concluidas': agg['concluidas'] or 0,
                'total': agg['total'] or 0,
            })
    else:
        if pessoa.eh_gestor and pessoa_id:
            pessoa_visualizada = get_object_or_404(Pessoa, id=pessoa_id)
        else:
            pessoa_visualizada = pessoa

        aproveitamentos = AproveitamentoDiario.objects.filter(
            pessoa=pessoa_visualizada,
            data__gte=data_inicio,
            data__lte=data_fim
        ).order_by('data')

        media_mes = aproveitamentos.aggregate(
            media=Avg('percentual'),
            tempo_total=Sum('tempo_total_segundos')
        )

        tarefas_nao_concluidas = ChecklistItem.objects.filter(
            responsavel=pessoa_visualizada,
            data_referencia__gte=data_inicio,
            data_referencia__lte=data_fim
        ).exclude(
            status=StatusItem.CONCLUIDO
        ).select_related('template', 'template__empresa', 'responsavel').order_by('-data_referencia')

        dados_grafico = []
        for dia in range(1, ultimo_dia + 1):
            data_dia = datetime(ano, mes, dia).date()
            aprov = aproveitamentos.filter(data=data_dia).first()
            dados_grafico.append({
                'dia': dia,
                'data': data_dia,
                'percentual': float(aprov.percentual) if aprov else None,
                'concluidas': aprov.tarefas_concluidas if aprov else 0,
                'total': aprov.total_tarefas if aprov else 0,
            })

    # Lista de meses para filtro
    meses = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]

    # Lista de pessoas (para gestor)
    pessoas_lista = []
    if pessoa.eh_gestor:
        pessoas_lista = Pessoa.objects.filter(
            empresas__in=get_empresas_filtradas(pessoa, request),
            ativo=True
        ).distinct()

    context = {
        'pessoa': pessoa,
        'pessoa_visualizada': pessoa_visualizada,
        'aproveitamentos': aproveitamentos,
        'tarefas_nao_concluidas': tarefas_nao_concluidas,
        'dados_grafico': dados_grafico,
        'media_mes': media_mes['media'] or 0,
        'tempo_total_mes': media_mes['tempo_total'] or 0,
        'mes': mes,
        'ano': ano,
        'meses': meses,
        'anos': range(2024, hoje.year + 2),
        'pessoas_lista': pessoas_lista,
        'ver_todos': ver_todos,
    }
    return render(request, 'checklists/aproveitamento.html', context)


@login_required
def aproveitamento_dia(request, data_str):
    """Detalhe do aproveitamento de um dia específico"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    try:
        data = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Data inválida')
        return redirect('aproveitamento')

    # Se é gestor, pode ver de outros
    pessoa_id = request.GET.get('pessoa')
    if pessoa.eh_gestor and pessoa_id:
        pessoa_visualizada = get_object_or_404(Pessoa, id=pessoa_id)
    else:
        pessoa_visualizada = pessoa

    # Buscar aproveitamento do dia
    aproveitamento = AproveitamentoDiario.objects.filter(
        pessoa=pessoa_visualizada,
        data=data
    ).first()

    # Buscar todas as tarefas do dia
    tarefas = ChecklistItem.objects.filter(
        responsavel=pessoa_visualizada,
        data_referencia=data
    ).select_related('template', 'template__empresa').order_by('ordem', 'template__ordem_execucao')

    context = {
        'pessoa': pessoa,
        'pessoa_visualizada': pessoa_visualizada,
        'data': data,
        'aproveitamento': aproveitamento,
        'tarefas': tarefas,
    }
    return render(request, 'checklists/aproveitamento_dia.html', context)


@login_required
def tarefas_pendentes_justificativa(request):
    """Lista tarefas que precisam de justificativa"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    hoje = timezone.localdate()

    # Tarefas não concluídas de dias anteriores sem justificativa
    tarefas = ChecklistItem.objects.filter(
        responsavel=pessoa,
        data_referencia__lt=hoje,
        dia_fechado=True,
        justificativa=''
    ).exclude(
        status=StatusItem.CONCLUIDO
    ).select_related('template', 'template__empresa').order_by('-data_referencia')

    context = {
        'pessoa': pessoa,
        'tarefas': tarefas,
    }
    return render(request, 'checklists/pendentes_justificativa.html', context)


# ============================================
# PROJETOS
# ============================================

@login_required
def lista_projetos(request):
    """Lista de projetos"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresa_filter = request.GET.get('empresa', '')
    status_filter = request.GET.get('status', '')

    empresas = get_empresas_filtradas(pessoa, request)

    if pessoa.eh_gestor:
        projetos = Projeto.objects.filter(empresa__in=empresas)
    else:
        projetos = Projeto.objects.filter(
            Q(responsavel=pessoa) | Q(participantes=pessoa),
            empresa__in=empresas,
        ).distinct()

    projetos = projetos.select_related('empresa', 'responsavel').prefetch_related('participantes')

    if empresa_filter:
        projetos = projetos.filter(empresa_id=empresa_filter)
    if status_filter:
        projetos = projetos.filter(status=status_filter)

    context = {
        'pessoa': pessoa,
        'projetos': projetos,
        'empresas': empresas,
        'status_choices': StatusProjeto.choices,
        'empresa_filter': empresa_filter,
        'status_filter': status_filter,
    }
    return render(request, 'checklists/lista_projetos.html', context)


@login_required
def lista_templates(request):
    """Lista de templates de projeto (apenas gestores)"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    if not pessoa.eh_gestor:
        messages.error(request, 'Apenas gestores podem acessar templates.')
        return redirect('lista_projetos')

    templates = ProjetoTemplate.objects.filter(ativo=True).prefetch_related('etapas')

    # Buscar templates globais vinculados a este tenant
    from tenants.models import ProjetoTemplateGlobal
    templates_globais = ProjetoTemplateGlobal.objects.filter(
        ativo=True
    ).prefetch_related('etapas').order_by('titulo')

    context = {
        'pessoa': pessoa,
        'templates': templates,
        'templates_globais': templates_globais,
    }
    return render(request, 'checklists/lista_templates.html', context)


@login_required
def mapa_mental_template(request, template_id):
    """Visualização do mapa mental de um template de projeto"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    template = get_object_or_404(ProjetoTemplate, id=template_id, ativo=True)
    etapas = template.etapas.all().order_by('ordem')

    context = {
        'pessoa': pessoa,
        'template': template,
        'etapas': etapas,
    }
    return render(request, 'checklists/mapa_mental_template.html', context)


@login_required
def criar_projeto(request):
    """Cria um novo projeto (apenas gestores)"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        messages.error(request, 'Apenas gestores podem criar projetos.')
        return redirect('lista_projetos')

    if request.method == 'POST':
        empresa_id = request.POST.get('empresa')
        responsavel_id = request.POST.get('responsavel')
        cliente_id = request.POST.get('cliente') or None
        template_id = request.POST.get('template') or None
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao', '')
        prazo = request.POST.get('prazo') or None
        status = request.POST.get('status', StatusProjeto.PLANEJAMENTO)
        cor = request.POST.get('cor', '#6366f1')
        dias_por_etapa = int(request.POST.get('dias_por_etapa', 7) or 7)

        if not all([empresa_id, titulo]):
            messages.error(request, 'Preencha todos os campos obrigatórios.')
        else:
            from tenants.models import ProjetoTemplateGlobal

            # Buscar template (local ou global) se selecionado
            template = None
            template_global = None
            etapas_template = []

            if template_id:
                # Verificar se é template global (prefixo 'global_')
                if template_id.startswith('global_'):
                    global_id = template_id.replace('global_', '')
                    template_global = ProjetoTemplateGlobal.objects.filter(id=global_id, ativo=True).first()
                    if template_global:
                        etapas_template = template_global.etapas.all().order_by('ordem')
                        if not cor:
                            cor = template_global.cor
                else:
                    template = ProjetoTemplate.objects.filter(id=template_id, ativo=True).first()
                    if template:
                        etapas_template = template.etapas.all().order_by('ordem')
                        if not cor:
                            cor = template.cor

            projeto = Projeto.objects.create(
                empresa_id=empresa_id,
                responsavel_id=responsavel_id or None,
                cliente_id=cliente_id,
                template_origem=template,  # Só armazena se for template local
                titulo=titulo,
                descricao=descricao,
                prazo=prazo,
                status=status,
                cor=cor,
            )
            participantes_ids = request.POST.getlist('participantes')
            if participantes_ids:
                projeto.participantes.set(participantes_ids)

            # Criar etapas a partir do template (local ou global)
            if etapas_template:
                hoje = timezone.localdate()
                for i, etapa in enumerate(etapas_template):
                    prazo_etapa = timezone.make_aware(
                        timezone.datetime.combine(
                            hoje + timedelta(days=dias_por_etapa * (i + 1)),
                            timezone.datetime.max.time()
                        )
                    )
                    Demanda.objects.create(
                        empresa_id=empresa_id,
                        projeto=projeto,
                        etapa_ordem=i + 1,
                        solicitante=pessoa,
                        responsavel_id=responsavel_id or None,
                        titulo=etapa.titulo,
                        descricao=etapa.descricao,
                        prazo=prazo_etapa,
                        tempo_estimado=etapa.tempo_estimado or 0,
                        tipo_etapa=TipoEtapa.DESENVOLVIMENTO,
                        status=StatusDemanda.PENDENTE,
                    )
                messages.success(request, f'Projeto "{titulo}" criado com {len(etapas_template)} etapas!')
            else:
                messages.success(request, f'Projeto "{titulo}" criado com sucesso!')

            return redirect('detalhe_projeto', projeto_id=projeto.id)

    empresas = get_empresas_filtradas(pessoa, request)
    pessoas = Pessoa.objects.filter(empresas__in=empresas, ativo=True).distinct()
    clientes = Cliente.objects.filter(empresa__in=empresas, ativo=True).order_by('nome')
    templates = ProjetoTemplate.objects.filter(ativo=True).order_by('titulo')

    # Buscar templates globais vinculados a este tenant
    from tenants.models import ProjetoTemplateGlobal
    templates_globais = ProjetoTemplateGlobal.objects.filter(
        ativo=True
    ).prefetch_related('etapas').order_by('titulo')

    context = {
        'pessoa': pessoa,
        'empresas': empresas,
        'pessoas': pessoas,
        'clientes': clientes,
        'templates': templates,
        'templates_globais': templates_globais,
        'status_choices': StatusProjeto.choices,
    }
    return render(request, 'checklists/criar_projeto.html', context)


@login_required
def detalhe_projeto(request, projeto_id):
    """Detalhe de um projeto com suas etapas"""
    projeto = get_object_or_404(Projeto, id=projeto_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa:
        return redirect('dashboard')

    empresas = get_empresas_filtradas(pessoa, request)
    tem_acesso = (
        projeto.empresa in empresas and pessoa.eh_gestor
    ) or projeto.responsavel == pessoa or pessoa in projeto.participantes.all()
    if not tem_acesso:
        messages.error(request, 'Você não tem acesso a este projeto.')
        return redirect('lista_projetos')

    todas_etapas = projeto.demandas.all().select_related('responsavel').order_by('etapa_ordem', 'criado_em')
    etapas_ativas = [e for e in todas_etapas if e.status != StatusDemanda.CONCLUIDO]
    etapas_concluidas = [e for e in todas_etapas if e.status == StatusDemanda.CONCLUIDO]

    participantes = projeto.participantes.all()

    context = {
        'projeto': projeto,
        'etapas_ativas': etapas_ativas,
        'etapas_concluidas': etapas_concluidas,
        'pessoa': pessoa,
        'participantes': participantes,
        'status_choices': StatusProjeto.choices,
    }
    return render(request, 'checklists/detalhe_projeto.html', context)


@login_required
def adicionar_etapa_projeto(request, projeto_id):
    """Adiciona uma etapa (demanda) ao projeto"""
    projeto = get_object_or_404(Projeto, id=projeto_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or not pessoa.eh_gestor:
        messages.error(request, 'Apenas gestores podem adicionar etapas.')
        return redirect('detalhe_projeto', projeto_id=projeto.id)

    if request.method == 'POST':
        responsavel_id = request.POST.get('responsavel')
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao', '')
        instrucoes = request.POST.get('instrucoes', '')
        prazo = request.POST.get('prazo')
        prioridade = request.POST.get('prioridade', PrioridadeDemanda.MEDIA)
        tipo_etapa = request.POST.get('tipo_etapa', TipoEtapa.DESENVOLVIMENTO)

        if not all([responsavel_id, titulo, prazo]):
            messages.error(request, 'Preencha todos os campos obrigatórios.')
        else:
            try:
                ultima_ordem = projeto.demandas.order_by('-etapa_ordem').first()
                ordem = (ultima_ordem.etapa_ordem + 1) if ultima_ordem else 1

                demanda = Demanda.objects.create(
                    empresa=projeto.empresa,
                    projeto=projeto,
                    etapa_ordem=ordem,
                    solicitante=pessoa,
                    responsavel_id=responsavel_id,
                    titulo=titulo,
                    descricao=descricao or '',
                    instrucoes=instrucoes or '',
                    prazo=prazo,
                    prioridade=prioridade,
                    tipo_etapa=tipo_etapa,
                )

                # Criar subtarefas do checklist
                checklist_items = request.POST.get('checklist_items', '')
                for i, linha in enumerate(checklist_items.strip().split('\n')):
                    linha = linha.strip()
                    if linha:
                        SubTarefaDemanda.objects.create(
                            demanda=demanda,
                            titulo=linha,
                            ordem=i,
                        )

                messages.success(request, f'Etapa "{titulo}" adicionada ao projeto!')
                return redirect('detalhe_projeto', projeto_id=projeto.id)
            except Exception as e:
                messages.error(request, f'Erro ao criar etapa: {e}')

    empresas = get_empresas_filtradas(pessoa, request)
    pessoas = Pessoa.objects.filter(empresas__id=projeto.empresa_id, ativo=True).distinct()

    context = {
        'projeto': projeto,
        'pessoa': pessoa,
        'pessoas': pessoas,
        'prioridades': PrioridadeDemanda.choices,
        'tipos_etapa': TipoEtapa.choices,
    }
    return render(request, 'checklists/adicionar_etapa.html', context)


@login_required
@require_POST
def gerenciar_participantes_projeto(request, projeto_id):
    """Adiciona/remove participantes de um projeto (apenas gestores)"""
    projeto = get_object_or_404(Projeto, id=projeto_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or not pessoa.eh_gestor:
        messages.error(request, 'Apenas gestores podem gerenciar participantes.')
        return redirect('detalhe_projeto', projeto_id=projeto.id)

    participantes_ids = request.POST.getlist('participantes')
    projeto.participantes.set(participantes_ids)
    messages.success(request, 'Participantes atualizados com sucesso!')
    return redirect('detalhe_projeto', projeto_id=projeto.id)


@login_required
@require_POST
@login_required
@require_POST
@login_required
@require_POST
def excluir_demanda(request, demanda_id):
    """Exclui uma demanda/pendência - apenas gestor"""
    demanda = get_object_or_404(Demanda, id=demanda_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa:
        return redirect('dashboard')

    empresas = get_empresas_filtradas(pessoa, request)
    pode_excluir = (request.user.is_staff or
                    (pessoa.eh_gestor and demanda.empresa in empresas))

    if not pode_excluir:
        messages.error(request, 'Você não tem permissão para excluir esta demanda.')
        return redirect('lista_demandas')

    titulo = demanda.titulo
    demanda.delete()
    messages.success(request, f'Demanda "{titulo}" excluída.')
    return redirect('lista_demandas')


def excluir_etapa_projeto(request, demanda_id):
    """Exclui uma etapa (demanda) do projeto"""
    demanda = get_object_or_404(Demanda, id=demanda_id, projeto__isnull=False)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa:
        return redirect('dashboard')

    empresas = get_empresas_filtradas(pessoa, request)
    pode_excluir = (request.user.is_staff or
                    (pessoa.eh_gestor and demanda.empresa in empresas))

    if not pode_excluir:
        messages.error(request, 'Você não tem permissão para excluir esta etapa.')
        return redirect('detalhe_projeto', projeto_id=demanda.projeto_id)

    projeto_id = demanda.projeto_id
    titulo = demanda.titulo
    demanda.delete()
    messages.success(request, f'Etapa "{titulo}" excluída com sucesso.')
    return redirect('detalhe_projeto', projeto_id=projeto_id)


@login_required
@require_POST
def excluir_tarefa(request, item_id):
    """Exclui uma tarefa da rotina diária - apenas gestor"""
    item = get_object_or_404(ChecklistItem, id=item_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Sem permissão'}, status=403)
        return redirect('dashboard')

    empresas = get_empresas_filtradas(pessoa, request)
    pode_excluir = (request.user.is_staff or
                    (pessoa.eh_gestor and item.template.empresa in empresas))

    if not pode_excluir:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Sem permissão'}, status=403)
        messages.error(request, 'Você não tem permissão para excluir esta tarefa.')
        return redirect('rotina_diaria')

    titulo = item.template.titulo
    item.delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'message': f'Tarefa "{titulo}" excluída.'})

    messages.success(request, f'Tarefa "{titulo}" excluída.')
    return redirect('rotina_diaria')


def mudar_status_projeto(request, projeto_id):
    """Muda o status de um projeto"""
    projeto = get_object_or_404(Projeto, id=projeto_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or not pessoa.eh_gestor:
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    novo_status = data.get('status')

    if novo_status not in [s[0] for s in StatusProjeto.choices]:
        return JsonResponse({'error': 'Status inválido'}, status=400)

    projeto.status = novo_status
    projeto.save()

    return JsonResponse({
        'status': 'ok',
        'novo_status': projeto.status,
        'status_display': projeto.get_status_display(),
    })


@login_required
@require_POST
def excluir_rotina_template(request, template_id):
    """Exclui uma rotina (ChecklistTemplate) e todas as tarefas geradas - apenas gestor"""
    template = get_object_or_404(ChecklistTemplate, id=template_id)
    pessoa = get_pessoa_or_redirect(request)

    pode_excluir = pessoa and (pessoa.is_gestor_empresa(template.empresa) or template.criado_por == pessoa)
    if not pode_excluir:
        messages.error(request, 'Sem permissao para excluir esta rotina.')
        return redirect('lista_rotinas')

    titulo = template.titulo
    template.delete()
    messages.success(request, f'Rotina "{titulo}" excluida com sucesso.')
    return redirect('lista_rotinas')


@login_required
@require_POST
def excluir_projeto(request, projeto_id):
    """Exclui um projeto (apenas admin)"""
    projeto = get_object_or_404(Projeto, id=projeto_id)

    # Apenas superusers (admin) podem excluir projetos
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Apenas administradores podem excluir projetos'}, status=403)

    data = json.loads(request.body) if request.body else {}
    excluir_etapas = data.get('excluir_etapas', False)

    titulo = projeto.titulo
    etapas_excluidas = 0

    if excluir_etapas:
        # Excluir todas as demandas/etapas do projeto
        etapas_excluidas = projeto.demandas.count()
        projeto.demandas.all().delete()

    projeto.delete()

    msg = f'Projeto "{titulo}" excluído'
    if excluir_etapas and etapas_excluidas > 0:
        msg += f' junto com {etapas_excluidas} etapa(s)'

    return JsonResponse({
        'status': 'ok',
        'message': msg,
        'etapas_excluidas': etapas_excluidas,
    })


# ============================================
# WAPI - WhatsApp Integration
# ============================================

@login_required
def wapi_painel(request):
    """Painel de configuração e controle do W-API"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        return redirect('dashboard')

    from notifications.wapi import WAPIClient
    from notifications.models import NotificacaoWhatsApp, AgendamentoNotificacao, DiaSemana

    client = WAPIClient()
    configurado = client.esta_configurado()

    # Criar agendamentos padrão se não existem
    defaults = [
        ('lembrete_diario', 'Lembrete Manhã', '08:00', 'seg,ter,qua,qui,sex'),
        ('lembrete_diario', 'Lembrete Tarde', '16:00', 'seg,ter,qua,qui,sex'),
        ('lembrete_diario', 'Lembrete Extra', '12:00', 'seg,ter,qua,qui,sex'),
        ('cobranca_funcionarios', 'Cobrança Funcionários', '17:00', 'seg,ter,qua,qui,sex'),
        ('cobranca_externos', 'Cobrança Externos', '09:00', 'seg,qui'),
        ('resumo_dependencias', 'Resumo Dependências', '08:30', 'seg,ter,qua,qui,sex'),
    ]
    for tipo, nome, horario, dias in defaults:
        if not AgendamentoNotificacao.objects.filter(tipo=tipo, nome=nome).exists():
            AgendamentoNotificacao.objects.create(
                tipo=tipo, nome=nome, horario=horario, dias_semana=dias, ativo=False
            )

    agendamentos = AgendamentoNotificacao.objects.all()

    # Últimas notificações (ordenadas por data, mais recentes primeiro)
    notificacoes = NotificacaoWhatsApp.objects.all().select_related('pessoa').order_by('-criado_em')[:20]

    # Estatísticas
    from django.db.models import Count
    hoje = timezone.localdate()
    stats = {
        'total_enviadas': NotificacaoWhatsApp.objects.filter(enviado=True).count(),
        'total_erros': NotificacaoWhatsApp.objects.filter(enviado=False).exclude(erro='').count(),
        'hoje_enviadas': NotificacaoWhatsApp.objects.filter(enviado=True, criado_em__date=hoje).count(),
    }

    # Pendências externas agrupadas por telefone
    from checklists.models import StatusItem, StatusDemanda
    pendencias_externas = {}

    tarefas_ext = ChecklistItem.objects.filter(
        status=StatusItem.DEPENDENTE,
        dependente_externo__gt='',
    ).select_related('template', 'responsavel')

    for t in tarefas_ext:
        tel = t.telefone_dependente_externo or 'sem-telefone'
        if tel not in pendencias_externas:
            pendencias_externas[tel] = {'nome': t.dependente_externo, 'telefone': t.telefone_dependente_externo, 'itens': []}
        pendencias_externas[tel]['itens'].append({
            'tipo': 'Tarefa',
            'titulo': t.template.titulo if t.template else 'Tarefa',
            'motivo': t.motivo_dependencia,
            'responsavel': t.responsavel.nome if t.responsavel else '',
        })

    demandas_ext = Demanda.objects.filter(
        status=StatusDemanda.DEPENDENTE,
        dependente_externo__gt='',
    ).select_related('responsavel')

    for d in demandas_ext:
        tel = d.telefone_dependente_externo or 'sem-telefone'
        if tel not in pendencias_externas:
            pendencias_externas[tel] = {'nome': d.dependente_externo, 'telefone': d.telefone_dependente_externo, 'itens': []}
        pendencias_externas[tel]['itens'].append({
            'tipo': 'Demanda',
            'titulo': d.titulo,
            'motivo': d.motivo_dependencia,
            'responsavel': d.responsavel.nome if d.responsavel else '',
        })

    # Pendências de funcionários agrupadas por pessoa
    pendencias_funcionarios = {}

    tarefas_func = ChecklistItem.objects.filter(
        data_referencia=hoje,
        status__in=[StatusItem.PENDENTE, StatusItem.EM_ANDAMENTO, StatusItem.ATRASADO],
        template__enviar_lembrete=True,
    ).select_related('template', 'responsavel')

    for t in tarefas_func:
        if not t.responsavel or not t.responsavel.telefone:
            continue
        pid = t.responsavel.id
        if pid not in pendencias_funcionarios:
            pendencias_funcionarios[pid] = {
                'nome': t.responsavel.nome,
                'telefone': t.responsavel.telefone,
                'itens': [],
            }
        status_label = t.get_status_display() if hasattr(t, 'get_status_display') else t.status
        pendencias_funcionarios[pid]['itens'].append({
            'titulo': t.template.titulo if t.template else 'Tarefa',
            'status': status_label,
        })

    context = {
        'pessoa': pessoa,
        'configurado': configurado,
        'notificacoes': notificacoes,
        'stats': stats,
        'wapi_instance': settings.WAPI_INSTANCE or 'Não configurado',
        'pendencias_externas': list(pendencias_externas.values()),
        'total_pendencias_externas': sum(len(p['itens']) for p in pendencias_externas.values()),
        'pendencias_funcionarios': list(pendencias_funcionarios.values()),
        'total_pendencias_funcionarios': sum(len(p['itens']) for p in pendencias_funcionarios.values()),
        'agendamentos': agendamentos,
        'dias_semana': DiaSemana.choices,
    }
    return render(request, 'checklists/wapi_painel.html', context)


@login_required
@require_POST
def wapi_status(request):
    """Verifica status da instância W-API"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    from notifications.wapi import WAPIClient
    client = WAPIClient()

    if not client.esta_configurado():
        return JsonResponse({'configured': False, 'error': 'W-API não configurada'})

    resultado = client.verificar_status()
    return JsonResponse({
        'configured': True,
        'connected': resultado.get('connected', False),
        'success': resultado.get('success', False),
        'data': resultado.get('data'),
        'error': resultado.get('error'),
    })


@login_required
@require_POST
def wapi_enviar_teste(request):
    """Envia mensagem de teste via W-API"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    telefone = data.get('telefone', '')
    mensagem = data.get('mensagem', '')

    if not telefone or not mensagem:
        return JsonResponse({'error': 'Telefone e mensagem são obrigatórios'}, status=400)

    # Formatar telefone
    telefone = ''.join(filter(str.isdigit, telefone))
    if not telefone.startswith('55'):
        telefone = '55' + telefone

    from notifications.wapi import WAPIClient
    from notifications.models import NotificacaoWhatsApp, TipoNotificacao

    client = WAPIClient()
    resultado = client.enviar_mensagem(telefone, mensagem)

    # Registrar no log
    NotificacaoWhatsApp.objects.create(
        pessoa=pessoa,
        tipo=TipoNotificacao.LEMBRETE,
        mensagem=f"[TESTE] {mensagem}",
        telefone=telefone,
        enviado=resultado['success'],
        enviado_em=timezone.now() if resultado['success'] else None,
        erro=resultado.get('error', ''),
    )

    return JsonResponse(resultado)


@login_required
@require_POST
def wapi_cobrar_dependencia(request):
    """Envia cobrança via WhatsApp para dependência externa"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    telefone = data.get('telefone', '')
    nome = data.get('nome', '')
    motivo = data.get('motivo', '')

    if not telefone:
        return JsonResponse({'error': 'Telefone é obrigatório'}, status=400)

    telefone = ''.join(filter(str.isdigit, telefone))
    if not telefone.startswith('55'):
        telefone = '55' + telefone

    mensagem = f"Olá {nome}! 👋\n\n"
    if motivo:
        mensagem += f"Estou aguardando: *{motivo}*\n\n"
    else:
        mensagem += "Estou aguardando um retorno seu sobre uma pendência.\n\n"
    mensagem += f"Pode me dar uma posição?\n\n*Neuraxo-Check - Mensagem Automática*"

    from notifications.wapi import WAPIClient
    from notifications.models import NotificacaoWhatsApp, TipoNotificacao

    client = WAPIClient()
    resultado = client.enviar_mensagem(telefone, mensagem)

    NotificacaoWhatsApp.objects.create(
        pessoa=pessoa,
        tipo=TipoNotificacao.COBRANCA,
        mensagem=mensagem,
        telefone=telefone,
        enviado=resultado['success'],
        enviado_em=timezone.now() if resultado['success'] else None,
        erro=resultado.get('error', ''),
    )

    return JsonResponse(resultado)


@login_required
@require_POST
def wapi_cobrar_todos(request):
    """Envia cobrança para TODAS as pessoas externas com pendências"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    from notifications.wapi import processar_cobrancas_externas
    resultado = processar_cobrancas_externas()
    return JsonResponse(resultado)


@login_required
@require_POST
def wapi_salvar_agendamentos(request):
    """Salva configurações de agendamento de notificações"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    from notifications.models import AgendamentoNotificacao

    data = json.loads(request.body)
    agendamentos = data.get('agendamentos', [])

    for ag in agendamentos:
        try:
            obj = AgendamentoNotificacao.objects.get(id=ag['id'])
            obj.ativo = ag.get('ativo', False)
            obj.horario = ag.get('horario', '09:00')
            obj.dias_semana = ag.get('dias_semana', '')
            obj.save()
        except AgendamentoNotificacao.DoesNotExist:
            continue

    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def wapi_executar_agendamento(request):
    """Executa manualmente um tipo de notificação"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    data = json.loads(request.body)
    tipo = data.get('tipo', '')

    from notifications.wapi import (
        processar_lembretes_diarios,
        processar_cobrancas,
        processar_cobrancas_externas,
        processar_resumo_dependencias,
        processar_contas_pagar,
    )

    executores = {
        'lembrete_diario': processar_lembretes_diarios,
        'cobranca_funcionarios': processar_cobrancas,
        'cobranca_externos': processar_cobrancas_externas,
        'resumo_dependencias': processar_resumo_dependencias,
        'contas_pagar': processar_contas_pagar,
    }

    executor = executores.get(tipo)
    if not executor:
        return JsonResponse({'error': f'Tipo inválido: {tipo}'}, status=400)

    resultado = executor()
    return JsonResponse(resultado)


# ============================================
# CRUD ROTINAS (ChecklistTemplate) - Gestores
# ============================================

@login_required
def lista_rotinas(request):
    """Lista rotinas recorrentes - gestores vêem todas, funcionários só as suas"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    if pessoa.eh_gestor:
        empresas = get_empresas_filtradas(pessoa, request)
        rotinas = ChecklistTemplate.objects.filter(empresa__in=empresas).select_related(
            'empresa', 'responsavel', 'cargo_responsavel'
        ).order_by('empresa__nome', 'ordem_execucao')
    else:
        rotinas = ChecklistTemplate.objects.filter(
            Q(responsavel=pessoa) | Q(cargo_responsavel=pessoa.cargo)
        ).select_related('empresa', 'responsavel', 'cargo_responsavel').order_by('ordem_execucao')

    # Solicitações de cancelamento pendentes (só gestor)
    cancelamentos_pendentes = []
    if pessoa.eh_gestor:
        empresas_ids = pessoa.empresas.values_list('id', flat=True)
        cancelamentos_pendentes = ChecklistItem.objects.filter(
            cancelamento_solicitado=True,
            template__empresa__in=empresas_ids,
        ).select_related('template', 'responsavel', 'template__empresa').order_by('-criado_em')

    context = {
        'pessoa': pessoa,
        'rotinas': rotinas,
        'cancelamentos_pendentes': cancelamentos_pendentes,
    }
    return render(request, 'checklists/lista_rotinas.html', context)


@login_required
def criar_rotina(request):
    """Cria nova rotina - gestores ou funcionários (funcionário só pra si mesmo)"""
    from .models import Recorrencia, DiaSemana
    from core.models import Cargo

    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('rotina_diaria')

    empresas = get_empresas_filtradas(pessoa, request)
    if pessoa.eh_gestor:
        pessoas = Pessoa.objects.filter(empresas__in=empresas).distinct()
    else:
        pessoas = Pessoa.objects.filter(id=pessoa.id)
    cargos = Cargo.objects.all() if pessoa.eh_gestor else Cargo.objects.none()

    if request.method == 'POST':
        empresa_id = request.POST.get('empresa')
        titulo = request.POST.get('titulo', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        processo = request.POST.get('processo', '').strip()
        recorrencia = request.POST.get('recorrencia', 'diaria')
        dia_semana = request.POST.get('dia_semana') or None
        dia_mes = request.POST.get('dia_mes') or None
        responsavel_val = request.POST.get('responsavel') or None
        cargo_id = request.POST.get('cargo_responsavel') or None
        horario_sugerido = request.POST.get('horario_sugerido') or None
        ordem = request.POST.get('ordem_execucao', 0) or 0
        tempo = request.POST.get('tempo_estimado', 0) or 0
        prioridade = request.POST.get('prioridade', 1) or 1

        dias_ativos = request.POST.getlist('dias_semana_ativos')

        # Funcionário só pode criar pra si mesmo
        if not pessoa.eh_gestor:
            responsavel_val = str(pessoa.id)
            cargo_id = None

        # Validar atribuição obrigatória
        if not responsavel_val and not cargo_id:
            messages.error(request, 'Selecione pelo menos um responsável ou cargo.')
        elif not titulo or not empresa_id:
            messages.error(request, 'Título e empresa são obrigatórios.')
        else:
            # Tratar opção "todos"
            responsavel_todos = responsavel_val == 'todos'
            responsavel_id = None if responsavel_todos or not responsavel_val else int(responsavel_val)

            template = ChecklistTemplate.objects.create(
                empresa_id=empresa_id,
                titulo=titulo,
                descricao=descricao,
                processo=processo,
                recorrencia=recorrencia,
                dia_semana=int(dia_semana) if dia_semana else None,
                dia_mes=int(dia_mes) if dia_mes else None,
                responsavel_id=responsavel_id,
                responsavel_todos=responsavel_todos,
                cargo_responsavel_id=int(cargo_id) if cargo_id else None,
                horario_sugerido=horario_sugerido,
                ordem_execucao=int(ordem),
                tempo_estimado=int(tempo),
                prioridade=int(prioridade),
                dias_semana_ativos=','.join(sorted(dias_ativos)) if dias_ativos else '0,1,2,3,4',
                criado_por=pessoa,
            )
            # Salvar subtarefas
            import json
            subtarefas_json = request.POST.get('subtarefas_json', '[]')
            try:
                subtarefas_list = json.loads(subtarefas_json)
                for i, titulo_sub in enumerate(subtarefas_list):
                    if titulo_sub.strip():
                        SubTarefaTemplate.objects.create(
                            template=template,
                            titulo=titulo_sub.strip(),
                            ordem=i,
                        )
            except (json.JSONDecodeError, TypeError):
                pass

            messages.success(request, f'Rotina "{titulo}" criada!')
            return redirect('lista_rotinas')

    context = {
        'pessoa': pessoa,
        'empresas': empresas,
        'pessoas': pessoas,
        'cargos': cargos,
        'recorrencias': Recorrencia.choices,
        'dias_semana': DiaSemana.choices,
        'tempos': ChecklistTemplate.TEMPO_ESTIMADO_CHOICES,
    }
    return render(request, 'checklists/criar_rotina.html', context)


@login_required
def editar_rotina(request, template_id):
    """Edita rotina existente - gestor ou criador da rotina"""
    from .models import Recorrencia, DiaSemana
    from core.models import Cargo

    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('rotina_diaria')

    template = get_object_or_404(ChecklistTemplate, id=template_id)

    # Funcionário só pode editar rotinas que ele criou
    pode_editar = pessoa.eh_gestor or template.criado_por == pessoa
    if not pode_editar:
        messages.error(request, 'Voce so pode editar rotinas que voce criou.')
        return redirect('lista_rotinas')

    empresas = get_empresas_filtradas(pessoa, request)
    if pessoa.eh_gestor:
        pessoas = Pessoa.objects.filter(empresas__in=empresas).distinct()
    else:
        pessoas = Pessoa.objects.filter(id=pessoa.id)
    cargos = Cargo.objects.all() if pessoa.eh_gestor else Cargo.objects.none()

    if request.method == 'POST':
        template.empresa_id = request.POST.get('empresa')
        template.titulo = request.POST.get('titulo', '').strip()
        template.descricao = request.POST.get('descricao', '').strip()
        template.processo = request.POST.get('processo', '').strip()
        template.recorrencia = request.POST.get('recorrencia', 'diaria')
        dia_semana = request.POST.get('dia_semana') or None
        dia_mes = request.POST.get('dia_mes') or None
        template.dia_semana = int(dia_semana) if dia_semana else None
        template.dia_mes = int(dia_mes) if dia_mes else None
        responsavel_val = request.POST.get('responsavel') or None
        cargo_id = request.POST.get('cargo_responsavel') or None

        # Validar atribuição obrigatória
        if not responsavel_val and not cargo_id:
            messages.error(request, 'Selecione pelo menos um responsável ou cargo.')
            return redirect('editar_rotina', template_id=template_id)

        # Tratar opção "todos"
        template.responsavel_todos = responsavel_val == 'todos'
        template.responsavel_id = None if template.responsavel_todos or not responsavel_val else int(responsavel_val)
        template.cargo_responsavel_id = int(cargo_id) if cargo_id else None
        template.horario_sugerido = request.POST.get('horario_sugerido') or None
        template.ordem_execucao = int(request.POST.get('ordem_execucao', 0) or 0)
        template.tempo_estimado = int(request.POST.get('tempo_estimado', 0) or 0)
        template.prioridade = int(request.POST.get('prioridade', 1) or 1)
        dias_ativos = request.POST.getlist('dias_semana_ativos')
        template.dias_semana_ativos = ','.join(sorted(dias_ativos)) if dias_ativos else '0,1,2,3,4'
        template.ativo = 'ativo' in request.POST
        template.save()

        # Atualizar subtarefas
        subtarefas_json = request.POST.get('subtarefas_json', '[]')
        try:
            subtarefas_list = json.loads(subtarefas_json)
            # Deletar as antigas e recriar
            template.subtarefas_template.all().delete()
            for i, titulo_sub in enumerate(subtarefas_list):
                if titulo_sub.strip():
                    SubTarefaTemplate.objects.create(
                        template=template,
                        titulo=titulo_sub.strip(),
                        ordem=i,
                    )
        except (json.JSONDecodeError, TypeError):
            pass

        messages.success(request, f'Rotina "{template.titulo}" atualizada!')
        return redirect('lista_rotinas')

    # Carregar subtarefas existentes
    subtarefas_existentes = list(
        template.subtarefas_template.order_by('ordem').values_list('titulo', flat=True)
    )

    context = {
        'pessoa': pessoa,
        'template': template,
        'empresas': empresas,
        'pessoas': pessoas,
        'cargos': cargos,
        'recorrencias': Recorrencia.choices,
        'dias_semana': DiaSemana.choices,
        'tempos': ChecklistTemplate.TEMPO_ESTIMADO_CHOICES,
        'subtarefas_existentes_json': json.dumps(subtarefas_existentes),
    }
    return render(request, 'checklists/editar_rotina.html', context)


# ============================================
# CALENDÁRIO
# ============================================

@login_required
def calendario(request):
    """Renderiza a página do calendário"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')
    return render(request, 'checklists/calendario.html', {'pessoa': pessoa})


@login_required
def calendario_eventos(request):
    """API JSON que retorna eventos do mês para o calendário"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return JsonResponse({'error': 'Usuário não vinculado'}, status=403)

    try:
        year = int(request.GET.get('year', timezone.localdate().year))
        month = int(request.GET.get('month', timezone.localdate().month))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Parâmetros inválidos'}, status=400)

    primeiro_dia = date(year, month, 1)
    ultimo_dia = date(year, month, calendar.monthrange(year, month)[1])
    agora = timezone.now()
    hoje = timezone.localdate()

    eventos = []

    is_gestor = pessoa.eh_gestor
    empresas = get_empresas_filtradas(pessoa, request)

    # 1. ChecklistItem (Tarefas)
    tarefas_qs = ChecklistItem.objects.filter(
        data_referencia__gte=primeiro_dia,
        data_referencia__lte=ultimo_dia,
    ).select_related('template', 'template__empresa', 'responsavel')

    if is_gestor:
        tarefas_qs = tarefas_qs.filter(template__empresa__in=empresas)
    else:
        tarefas_qs = tarefas_qs.filter(responsavel=pessoa)

    for t in tarefas_qs:
        atrasado = t.status not in (StatusItem.CONCLUIDO, StatusItem.CANCELADO) and t.data_referencia < hoje
        eventos.append({
            'id': t.id,
            'type': 'tarefa',
            'title': t.template.titulo if t.template else 'Tarefa',
            'date': t.data_referencia.isoformat(),
            'status': t.get_status_display(),
            'color': '#3b82f6',
            'url': f'/tarefa/{t.id}/',
            'responsavel': t.responsavel.nome if t.responsavel else '',
            'overdue': atrasado,
            'concluido': t.status == StatusItem.CONCLUIDO,
        })

    # 2. Demandas
    from datetime import datetime, time as dt_time
    inicio_mes = timezone.make_aware(datetime.combine(primeiro_dia, dt_time.min))
    fim_mes = timezone.make_aware(datetime.combine(ultimo_dia, dt_time.max))

    demandas_qs = Demanda.objects.filter(
        prazo__gte=inicio_mes,
        prazo__lte=fim_mes,
    ).select_related('empresa', 'responsavel')

    if is_gestor:
        demandas_qs = demandas_qs.filter(empresa__in=empresas)
    else:
        demandas_qs = demandas_qs.filter(responsavel=pessoa)

    for d in demandas_qs:
        is_urgente = d.prioridade == PrioridadeDemanda.URGENTE
        atrasado = d.status not in (StatusDemanda.CONCLUIDO, StatusDemanda.CANCELADO) and d.prazo < agora
        eventos.append({
            'id': d.id,
            'type': 'demanda',
            'title': d.titulo,
            'date': d.prazo.date().isoformat() if d.prazo else '',
            'status': d.get_status_display(),
            'color': '#ef4444' if is_urgente else '#f97316',
            'url': f'/demanda/{d.id}/',
            'responsavel': d.responsavel.nome if d.responsavel else '',
            'overdue': atrasado,
            'concluido': d.status == StatusDemanda.CONCLUIDO,
        })

    # 3. ContaPagarItem (Contas a Pagar)
    from financeiro.models import ContaPagarItem
    contas_qs = ContaPagarItem.objects.filter(
        data_vencimento__gte=primeiro_dia,
        data_vencimento__lte=ultimo_dia,
    ).select_related('conta_pagar', 'conta_pagar__empresa')

    if is_gestor:
        contas_qs = contas_qs.filter(conta_pagar__empresa__in=empresas)
    else:
        # Funcionário não vê contas a pagar (sem campo responsavel)
        contas_qs = contas_qs.none()

    for c in contas_qs:
        atrasado = not c.pago and c.data_vencimento < hoje
        eventos.append({
            'id': c.id,
            'type': 'conta',
            'title': c.conta_pagar.descricao if c.conta_pagar else 'Conta',
            'date': c.data_vencimento.isoformat(),
            'status': 'Pago' if c.pago else 'Pendente',
            'color': '#10b981',
            'url': f'/financeiro/',
            'responsavel': '',
            'overdue': atrasado,
            'concluido': c.pago,
        })

    # 4. Projetos (com prazo)
    projetos_qs = Projeto.objects.filter(
        prazo__gte=primeiro_dia,
        prazo__lte=ultimo_dia,
    ).select_related('empresa', 'responsavel')

    if is_gestor:
        projetos_qs = projetos_qs.filter(empresa__in=empresas)
    else:
        projetos_qs = projetos_qs.filter(
            Q(responsavel=pessoa) | Q(participantes=pessoa)
        ).distinct()

    for p in projetos_qs:
        atrasado = p.status not in (StatusProjeto.CONCLUIDO, StatusProjeto.CANCELADO) and p.prazo and p.prazo < hoje
        eventos.append({
            'id': p.id,
            'type': 'projeto',
            'title': p.titulo,
            'date': p.prazo.isoformat() if p.prazo else '',
            'status': p.get_status_display(),
            'color': '#a855f7',
            'url': f'/projeto/{p.id}/',
            'responsavel': p.responsavel.nome if p.responsavel else '',
            'overdue': atrasado,
            'concluido': p.status == StatusProjeto.CONCLUIDO,
        })

    return JsonResponse({'eventos': eventos})


# ============================================
# MAPA MENTAL DO PROJETO
# ============================================

@login_required
def mapa_mental_projeto(request, projeto_id):
    """Visualização do mapa mental do projeto"""
    projeto = get_object_or_404(Projeto, id=projeto_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa:
        return redirect('dashboard')

    empresas = get_empresas_filtradas(pessoa, request)
    tem_acesso = (
        projeto.empresa in empresas and pessoa.eh_gestor
    ) or projeto.responsavel == pessoa or pessoa in projeto.participantes.all()

    if not tem_acesso:
        messages.error(request, 'Você não tem acesso a este projeto.')
        return redirect('lista_projetos')

    # Buscar etapas com subtarefas e nós extras
    etapas = projeto.demandas.prefetch_related('subtarefas_demanda').all().order_by('etapa_ordem')
    nos_extras = projeto.nos_mapa.all()

    context = {
        'projeto': projeto,
        'pessoa': pessoa,
        'etapas': etapas,
        'nos_extras': nos_extras,
        'tipos_no': TipoNoMapa.choices,
        'status_cores': {
            'pendente': '#9ca3af',
            'em_andamento': '#3b82f6',
            'dependente': '#f97316',
            'concluido': '#22c55e',
            'cancelado': '#ef4444',
        },
        'tipo_etapa_cores': {
            'desenvolvimento': '#3b82f6',
            'melhoria': '#10b981',
        },
    }
    return render(request, 'checklists/mapa_mental.html', context)


@login_required
@require_POST
def adicionar_no_mapa(request, projeto_id):
    """Adiciona um nó extra ao mapa mental"""
    projeto = get_object_or_404(Projeto, id=projeto_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or not pessoa.eh_gestor:
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    try:
        data = json.loads(request.body)
        tipo = data.get('tipo', TipoNoMapa.IDEIA)
        titulo = data.get('titulo', '').strip()
        descricao = data.get('descricao', '')
        cor = data.get('cor', '#94a3b8')
        url = data.get('url', '')
        conectado_a_etapa_id = data.get('conectado_a_etapa')
        posicao_x = data.get('posicao_x', 0)
        posicao_y = data.get('posicao_y', 0)

        if not titulo:
            return JsonResponse({'error': 'Título é obrigatório'}, status=400)

        no = MapaMentalNo.objects.create(
            projeto=projeto,
            tipo=tipo,
            titulo=titulo,
            descricao=descricao,
            cor=cor,
            url=url,
            conectado_a_etapa_id=conectado_a_etapa_id if conectado_a_etapa_id else None,
            posicao_x=posicao_x,
            posicao_y=posicao_y,
        )

        return JsonResponse({
            'status': 'ok',
            'no': {
                'id': no.id,
                'tipo': no.tipo,
                'titulo': no.titulo,
                'descricao': no.descricao,
                'cor': no.cor,
                'url': no.url,
                'conectado_a_etapa': no.conectado_a_etapa_id,
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def excluir_no_mapa(request, no_id):
    """Exclui um nó do mapa mental"""
    no = get_object_or_404(MapaMentalNo, id=no_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or not pessoa.eh_gestor:
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    no.delete()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def editar_no_mapa(request, no_id):
    """Edita um nó do mapa mental"""
    no = get_object_or_404(MapaMentalNo, id=no_id)
    pessoa = get_pessoa_or_redirect(request)

    if not pessoa or not pessoa.eh_gestor:
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    try:
        data = json.loads(request.body)

        if 'titulo' in data:
            no.titulo = data['titulo'].strip()
        if 'descricao' in data:
            no.descricao = data['descricao']
        if 'tipo' in data:
            no.tipo = data['tipo']
        if 'cor' in data:
            no.cor = data['cor']
        if 'url' in data:
            no.url = data['url']
        if 'conectado_a_etapa' in data:
            no.conectado_a_etapa_id = data['conectado_a_etapa'] if data['conectado_a_etapa'] else None
        if 'posicao_x' in data:
            no.posicao_x = data['posicao_x']
        if 'posicao_y' in data:
            no.posicao_y = data['posicao_y']

        no.save()

        return JsonResponse({
            'status': 'ok',
            'no': {
                'id': no.id,
                'tipo': no.tipo,
                'titulo': no.titulo,
                'descricao': no.descricao,
                'cor': no.cor,
                'url': no.url,
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================
# ANOTAÇÕES / BLOCO DE NOTAS PESSOAL
# ============================================

@login_required
def anotacoes(request):
    """Lista e cria anotações pessoais"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        messages.warning(request, 'Seu usuário não está vinculado a uma pessoa.')
        return redirect('dashboard')

    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        conteudo = request.POST.get('conteudo', '').strip()
        cor = request.POST.get('cor', '#fef3c7')
        if titulo and conteudo:
            Anotacao.objects.create(pessoa=pessoa, titulo=titulo, conteudo=conteudo, cor=cor)
            messages.success(request, 'Anotação criada!')
        else:
            messages.error(request, 'Título e conteúdo são obrigatórios.')
        return redirect('anotacoes')

    q = request.GET.get('q', '').strip()
    notas = Anotacao.objects.filter(pessoa=pessoa)
    if q:
        notas = notas.filter(Q(titulo__icontains=q) | Q(conteudo__icontains=q))

    return render(request, 'checklists/anotacoes.html', {
        'notas': notas,
        'q': q,
    })


@login_required
@require_POST
def editar_anotacao(request, anotacao_id):
    """Edita uma anotação existente"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return JsonResponse({'error': 'Sem vínculo'}, status=403)

    anotacao = get_object_or_404(Anotacao, id=anotacao_id, pessoa=pessoa)
    titulo = request.POST.get('titulo', '').strip()
    conteudo = request.POST.get('conteudo', '').strip()
    cor = request.POST.get('cor', anotacao.cor)

    if titulo and conteudo:
        anotacao.titulo = titulo
        anotacao.conteudo = conteudo
        anotacao.cor = cor
        anotacao.save()
        messages.success(request, 'Anotação atualizada!')
    else:
        messages.error(request, 'Título e conteúdo são obrigatórios.')

    return redirect('anotacoes')


@login_required
@require_POST
def excluir_anotacao(request, anotacao_id):
    """Exclui uma anotação"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return JsonResponse({'error': 'Sem vínculo'}, status=403)

    anotacao = get_object_or_404(Anotacao, id=anotacao_id, pessoa=pessoa)
    anotacao.delete()
    messages.success(request, 'Anotação excluída!')
    return redirect('anotacoes')


@login_required
@require_POST
def fixar_anotacao(request, anotacao_id):
    """Toggle fixar/desafixar anotação"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return JsonResponse({'error': 'Sem vínculo'}, status=403)

    anotacao = get_object_or_404(Anotacao, id=anotacao_id, pessoa=pessoa)
    anotacao.fixado = not anotacao.fixado
    anotacao.save()
    return redirect('anotacoes')


# ============================================
# COFRE DE SENHAS
# ============================================

@login_required
def cofre(request):
    """Lista credenciais do cofre de senhas"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        messages.warning(request, 'Seu usuário não está vinculado a uma pessoa.')
        return redirect('dashboard')

    # Verificar se o cofre está desbloqueado na sessão
    cofre_desbloqueado = request.session.get('cofre_desbloqueado', False)

    if request.method == 'POST' and 'cofre_senha' in request.POST:
        from django.contrib.auth import authenticate
        senha = request.POST.get('cofre_senha', '')
        user = authenticate(username=request.user.username, password=senha)
        if user is not None:
            request.session['cofre_desbloqueado'] = True
            cofre_desbloqueado = True
        else:
            messages.error(request, 'Senha incorreta.')
            return render(request, 'checklists/cofre_login.html', {'pessoa': pessoa})

    if not cofre_desbloqueado:
        return render(request, 'checklists/cofre_login.html', {'pessoa': pessoa})

    # Empresas que o usuário tem acesso (filtrado pela empresa ativa)
    empresas = get_empresas_filtradas(pessoa, request)

    # Filtro por empresa
    empresa_id = request.GET.get('empresa', '')
    categoria = request.GET.get('categoria', '')
    q = request.GET.get('q', '').strip()

    cliente_id = request.GET.get('cliente', '')

    itens = ItemCofre.objects.filter(empresa__in=empresas).select_related('empresa', 'criado_por', 'cliente')

    # Permissão: gestor vê tudo, outros só o que criaram ou foi compartilhado com eles
    if not pessoa.eh_gestor:
        itens = itens.filter(Q(criado_por=pessoa) | Q(compartilhado_com=pessoa)).distinct()

    if empresa_id:
        itens = itens.filter(empresa_id=empresa_id)
    if cliente_id:
        itens = itens.filter(cliente_id=cliente_id)
    if categoria:
        itens = itens.filter(categoria=categoria)
    if q:
        itens = itens.filter(Q(titulo__icontains=q) | Q(usuario__icontains=q) | Q(url__icontains=q) | Q(notas__icontains=q))

    clientes = Cliente.objects.filter(empresa__in=empresas, ativo=True).order_by('nome')

    # Agrupar por cliente
    itens_por_cliente = {}
    itens_internos = []
    for item in itens:
        if item.cliente:
            nome = item.cliente.nome
            if nome not in itens_por_cliente:
                itens_por_cliente[nome] = {'cliente': item.cliente, 'itens': []}
            itens_por_cliente[nome]['itens'].append(item)
        else:
            itens_internos.append(item)

    vista = request.GET.get('vista', 'todos')

    # Funcionários pra compartilhamento (só gestor vê)
    funcionarios_cofre = []
    if pessoa.eh_gestor:
        funcionarios_cofre = Pessoa.objects.filter(
            empresas__in=empresas, ativo=True
        ).exclude(id=pessoa.id).distinct().order_by('nome')

    return render(request, 'checklists/cofre.html', {
        'itens': itens,
        'empresas': empresas,
        'empresa_id': empresa_id,
        'cliente_id': cliente_id,
        'clientes': clientes,
        'categoria_selecionada': categoria,
        'categorias': CategoriaCofre.choices,
        'q': q,
        'vista': vista,
        'itens_por_cliente': itens_por_cliente,
        'itens_internos': itens_internos,
        'funcionarios_cofre': funcionarios_cofre,
    })


@login_required
@require_POST
def cofre_criar(request):
    """Cria uma nova credencial no cofre"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresa_id = request.POST.get('empresa')
    titulo = request.POST.get('titulo', '').strip()
    categoria = request.POST.get('categoria', 'site')
    url = request.POST.get('url', '').strip()
    usuario = request.POST.get('usuario', '').strip()
    senha = request.POST.get('senha', '').strip()
    notas = request.POST.get('notas', '').strip()

    if not titulo or not empresa_id:
        messages.error(request, 'Título e empresa são obrigatórios.')
        return redirect('cofre')

    # Verificar acesso à empresa
    if pessoa.eh_gestor:
        empresa = get_object_or_404(Empresa, id=empresa_id, ativo=True)
    else:
        empresa = get_object_or_404(Empresa, id=empresa_id, ativo=True, pessoas=pessoa)

    cliente_id = request.POST.get('cliente') or None

    item = ItemCofre(
        empresa=empresa,
        cliente_id=cliente_id,
        titulo=titulo,
        categoria=categoria,
        url=url,
        usuario=usuario,
        notas=notas,
        criado_por=pessoa,
    )
    item.set_senha(senha)
    item.save()

    # Compartilhar com funcionários selecionados
    compartilhar_ids = request.POST.getlist('compartilhado_com')
    if compartilhar_ids:
        item.compartilhado_com.set(compartilhar_ids)

    messages.success(request, 'Credencial adicionada ao cofre!')
    return redirect('cofre')


@login_required
@require_POST
def cofre_editar(request, item_id):
    """Edita uma credencial do cofre"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    # Verificar acesso
    empresas = pessoa.empresas.filter(ativo=True)

    item = get_object_or_404(ItemCofre, id=item_id, empresa__in=empresas)

    titulo = request.POST.get('titulo', '').strip()
    categoria = request.POST.get('categoria', item.categoria)
    empresa_id = request.POST.get('empresa', '')
    url = request.POST.get('url', '').strip()
    usuario = request.POST.get('usuario', '').strip()
    senha = request.POST.get('senha', '').strip()
    notas = request.POST.get('notas', '').strip()

    if not titulo:
        messages.error(request, 'Título é obrigatório.')
        return redirect('cofre')

    # Trocar empresa se fornecida e diferente
    if empresa_id and str(item.empresa_id) != empresa_id:
        nova_empresa = get_object_or_404(Empresa, id=empresa_id, ativo=True)
        if not pessoa.eh_gestor and not pessoa.empresas.filter(id=nova_empresa.id).exists():
            messages.error(request, 'Sem acesso a esta empresa.')
            return redirect('cofre')
        item.empresa = nova_empresa

    item.titulo = titulo
    item.categoria = categoria
    item.url = url
    item.usuario = usuario
    item.notas = notas
    # Só atualiza senha se fornecida (campo não vazio)
    if senha:
        item.set_senha(senha)
    item.save()

    # Atualizar compartilhamento
    compartilhar_ids = request.POST.getlist('compartilhado_com')
    item.compartilhado_com.set(compartilhar_ids)

    messages.success(request, 'Credencial atualizada!')
    return redirect('cofre')


@login_required
@require_POST
def cofre_excluir(request, item_id):
    """Exclui uma credencial do cofre"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = pessoa.empresas.filter(ativo=True)

    item = get_object_or_404(ItemCofre, id=item_id, empresa__in=empresas)
    item.delete()
    messages.success(request, 'Credencial excluída!')
    return redirect('cofre')


@login_required
def cofre_ver_senha(request, item_id):
    """Retorna a senha descriptografada via AJAX (JSON)"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return JsonResponse({'error': 'Sem vínculo'}, status=403)

    empresas = pessoa.empresas.filter(ativo=True)

    # Verificar se cofre está desbloqueado
    if not request.session.get('cofre_desbloqueado', False):
        return JsonResponse({'error': 'Cofre bloqueado'}, status=403)

    item = get_object_or_404(ItemCofre, id=item_id, empresa__in=empresas)

    # Permissão: gestor, criador ou compartilhado
    if not pessoa.eh_gestor and item.criado_por != pessoa and not item.compartilhado_com.filter(id=pessoa.id).exists():
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    return JsonResponse({'senha': item.get_senha()})


@login_required
@require_POST
def cofre_bloquear(request):
    """Bloqueia o cofre (remove desbloqueio da sessão)"""
    request.session.pop('cofre_desbloqueado', None)
    return redirect('cofre')


# ============================================
# REORDENAR ROTINAS (drag & drop)
# ============================================

@login_required
@require_POST
def reordenar_rotinas(request):
    """API para reordenar rotinas via drag & drop"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        return JsonResponse({'error': 'Sem permissão'}, status=403)

    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        for item in items:
            ChecklistTemplate.objects.filter(id=item['id']).update(
                ordem_execucao=item['ordem']
            )
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ============================================
# NOTIFICAÇÕES IN-APP
# ============================================

@login_required
def notificacoes(request):
    """Lista notificações do usuário"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    notifs = pessoa.notificacoes_inapp.all()[:50]
    nao_lidas = pessoa.notificacoes_inapp.filter(lida=False).count()

    return render(request, 'checklists/notificacoes.html', {
        'notificacoes': notifs,
        'nao_lidas': nao_lidas,
    })


@login_required
def notificacoes_count(request):
    """API: retorna contagem de não lidas (polling)"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return JsonResponse({'count': 0})
    count = pessoa.notificacoes_inapp.filter(lida=False).count()
    return JsonResponse({'count': count})


@login_required
@require_POST
def notificacao_marcar_lida(request, notif_id):
    """Marca notificação como lida e redireciona"""
    from core.models import NotificacaoInApp
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    notif = get_object_or_404(NotificacaoInApp, id=notif_id, destinatario=pessoa)
    notif.lida = True
    notif.save(update_fields=['lida'])

    if notif.url:
        return redirect(notif.url)
    return redirect('notificacoes')


@login_required
@require_POST
def notificacoes_marcar_todas(request):
    """Marca todas como lidas"""
    pessoa = get_pessoa_or_redirect(request)
    if pessoa:
        pessoa.notificacoes_inapp.filter(lida=False).update(lida=True)
    return redirect('notificacoes')


# ============================================
# EQUIPE - Gestão de Usuários
# ============================================

@login_required
def equipe(request):
    """Lista membros da equipe com seus papéis por empresa"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        messages.error(request, 'Apenas gestores podem gerenciar a equipe.')
        return redirect('dashboard')

    empresas = get_empresas_filtradas(pessoa, request)
    membros = Pessoa.objects.filter(
        empresas__in=empresas, ativo=True
    ).distinct().select_related('user', 'cargo').prefetch_related('empresas', 'empresas_gestor')

    membros_dados = []
    for m in membros:
        emps_dados = []
        for emp in m.empresas.filter(id__in=empresas).order_by('nome'):
            papel = m.get_papel_empresa(emp)
            emps_dados.append({
                'empresa': emp,
                'papel': papel,
                'is_gestor': papel == 'gestor',
            })
        membros_dados.append({
            'pessoa': m,
            'email': m.user.email if m.user else '',
            'username': m.user.username if m.user else '',
            'is_active': m.user.is_active if m.user else False,
            'empresas': emps_dados,
        })

    context = {
        'pessoa': pessoa,
        'membros': membros_dados,
        'empresas': empresas,
        'total_membros': len(membros_dados),
    }
    return render(request, 'checklists/equipe.html', context)


@login_required
@require_POST
def convidar_membro(request):
    """Convida novo membro por email"""
    from django.contrib.auth.models import User
    import secrets

    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        return redirect('dashboard')

    email = request.POST.get('email', '').strip().lower()
    nome = request.POST.get('nome', '').strip()
    empresa_ids = request.POST.getlist('empresas')
    papel = request.POST.get('papel', 'funcionario')

    if not email or not nome or not empresa_ids:
        messages.error(request, 'Nome, email e pelo menos uma empresa são obrigatórios.')
        return redirect('equipe')

    from core.models import PapelEmpresa

    # Verificar se email já existe
    user_existente = User.objects.filter(email__iexact=email).first()
    if user_existente:
        pessoa_existente = Pessoa.objects.filter(user=user_existente).first()
        if pessoa_existente:
            for eid in empresa_ids:
                emp = Empresa.objects.filter(id=eid).first()
                if emp:
                    pessoa_existente.empresas.add(emp)
                    PapelEmpresa.objects.update_or_create(
                        pessoa=pessoa_existente, empresa=emp,
                        defaults={'papel': papel}
                    )
            messages.success(request, f'{nome} já existe e foi adicionado às empresas selecionadas.')
            return redirect('equipe')

    # Criar novo usuário
    senha_temp = secrets.token_urlsafe(8)
    username = email.split('@')[0]
    base_username = username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f'{base_username}{counter}'
        counter += 1

    user = User.objects.create_user(
        username=username,
        email=email,
        password=senha_temp,
    )

    nova_pessoa = Pessoa.objects.create(
        user=user,
        nome=nome,
        email=email,
        ativo=True,
    )

    for eid in empresa_ids:
        emp = Empresa.objects.filter(id=eid).first()
        if emp:
            nova_pessoa.empresas.add(emp)
            PapelEmpresa.objects.create(
                pessoa=nova_pessoa, empresa=emp, papel=papel
            )

    messages.success(request, f'{nome} convidado! Senha temporária: {senha_temp}')
    return redirect('equipe')


@login_required
@require_POST
def editar_membro(request, pessoa_id):
    """Edita papel de um membro nas empresas"""
    pessoa_logada = get_pessoa_or_redirect(request)
    if not pessoa_logada or not pessoa_logada.is_gestor:
        return redirect('dashboard')

    from core.models import PapelEmpresa

    membro = get_object_or_404(Pessoa, id=pessoa_id, ativo=True)
    empresas_gestor = pessoa_logada.empresas.filter(ativo=True)

    for emp in empresas_gestor:
        papel = request.POST.get(f'papel_{emp.id}')
        if papel in ('gestor', 'colaborador', 'executante'):
            membro.empresas.add(emp)
            PapelEmpresa.objects.update_or_create(
                pessoa=membro, empresa=emp,
                defaults={'papel': papel}
            )
        elif papel == 'remover':
            membro.empresas.remove(emp)
            PapelEmpresa.objects.filter(pessoa=membro, empresa=emp).delete()

    messages.success(request, f'Permissões de {membro.nome} atualizadas.')
    return redirect('equipe')


# ============================================
# EMPRESAS
# ============================================

@login_required
def lista_empresas(request):
    """Lista empresas do usuário com opção de criar"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        return redirect('dashboard')

    empresas = pessoa.empresas.filter(ativo=True).order_by('nome')
    empresas_dados = []
    for emp in empresas:
        papel = pessoa.get_papel_empresa(emp)
        pessoas_count = Pessoa.objects.filter(empresas=emp, ativo=True).count()
        empresas_dados.append({
            'empresa': emp,
            'papel': papel,
            'pessoas': pessoas_count,
        })

    return render(request, 'checklists/empresas.html', {
        'pessoa': pessoa,
        'empresas': empresas_dados,
    })


@login_required
@require_POST
def criar_empresa(request):
    """Cria nova empresa e vincula ao usuário"""
    from core.models import PapelEmpresa
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        return redirect('dashboard')

    nome = request.POST.get('nome', '').strip()
    cor = request.POST.get('cor', '#6366f1')

    if not nome:
        messages.error(request, 'Nome é obrigatório.')
        return redirect('lista_empresas')

    if Empresa.objects.filter(nome__iexact=nome).exists():
        messages.error(request, f'Empresa "{nome}" já existe.')
        return redirect('lista_empresas')

    emp = Empresa.objects.create(nome=nome, cor=cor)
    pessoa.empresas.add(emp)
    pessoa.empresas_gestor.add(emp)
    PapelEmpresa.objects.create(pessoa=pessoa, empresa=emp, papel='gestor')

    messages.success(request, f'Empresa "{nome}" criada!')
    return redirect('lista_empresas')


@login_required
@require_POST
def editar_empresa(request, empresa_id):
    """Edita nome/cor de uma empresa"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    emp = get_object_or_404(Empresa, id=empresa_id)
    if not pessoa.is_gestor_empresa(emp):
        messages.error(request, 'Sem permissão.')
        return redirect('lista_empresas')

    nome = request.POST.get('nome', '').strip()
    cor = request.POST.get('cor', emp.cor)

    if nome:
        emp.nome = nome
    emp.cor = cor
    emp.save()

    messages.success(request, f'Empresa "{emp.nome}" atualizada!')
    return redirect('lista_empresas')


# ============================================
# CLIENTES E SOLICITAÇÕES
# ============================================

@login_required
def clientes_dashboard(request):
    """Dashboard de clientes com pendências"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = get_empresas_filtradas(pessoa, request)
    clientes = Cliente.objects.filter(empresa__in=empresas, ativo=True).order_by('nome')

    from core.models import Solicitacao
    # Stats
    total_solicitacoes = Solicitacao.objects.filter(empresa__in=empresas).exclude(status='cancelado')
    pendentes = total_solicitacoes.filter(status__in=['pendente', 'em_andamento']).count()
    atrasadas = total_solicitacoes.filter(status__in=['pendente', 'em_andamento'], prazo__lt=timezone.now()).count()
    concluidas = total_solicitacoes.filter(status='concluido').count()

    # Clientes com pendências
    clientes_dados = []
    for c in clientes:
        pend = c.get_pendencias_count()
        atras = c.get_atrasadas_count()
        clientes_dados.append({
            'cliente': c,
            'pendencias': pend,
            'atrasadas': atras,
        })
    # Ordenar: atrasados primeiro
    clientes_dados.sort(key=lambda x: (-x['atrasadas'], -x['pendencias']))

    # Solicitações atrasadas (urgentes)
    sol_atrasadas = Solicitacao.objects.filter(
        empresa__in=empresas, status__in=['pendente', 'em_andamento'],
        prazo__lt=timezone.now(),
    ).select_related('cliente', 'contato', 'empresa').order_by('prazo')

    # Últimas solicitações
    ultimas = Solicitacao.objects.filter(
        empresa__in=empresas
    ).select_related('cliente', 'empresa', 'contato').order_by('-criado_em')[:10]

    # Respondidas recentemente (cliente respondeu, voce precisa ver)
    from core.models import ComentarioSolicitacao
    respostas_recentes = ComentarioSolicitacao.objects.filter(
        solicitacao__empresa__in=empresas,
        autor_is_cliente=True,
    ).select_related('solicitacao', 'solicitacao__cliente').order_by('-criado_em')[:5]

    # Stats financeiros
    from django.db.models import Sum
    receita_mensal = clientes.filter(status_contrato='ativo').aggregate(
        total=Sum('valor_mensal'))['total'] or 0
    inadimplentes = clientes.filter(status_contrato='inadimplente')
    inadimplentes_count = inadimplentes.count()
    inadimplentes_valor = inadimplentes.aggregate(total=Sum('valor_mensal'))['total'] or 0

    context = {
        'pessoa': pessoa,
        'clientes': clientes_dados,
        'total_clientes': clientes.count(),
        'pendentes': pendentes,
        'atrasadas': atrasadas,
        'concluidas': concluidas,
        'sol_atrasadas': sol_atrasadas,
        'ultimas': ultimas,
        'respostas_recentes': respostas_recentes,
        'empresas': empresas,
        'receita_mensal': receita_mensal,
        'inadimplentes_count': inadimplentes_count,
        'inadimplentes_valor': inadimplentes_valor,
        'clientes_ativos': clientes.filter(status_contrato='ativo').count(),
        'clientes_pausados': clientes.filter(status_contrato='pausado').count(),
    }
    return render(request, 'checklists/clientes_dashboard.html', context)


@login_required
def cliente_detalhe(request, cliente_id):
    """Detalhe de um cliente com suas solicitações"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    from core.models import Solicitacao, TipoSolicitacao, StatusSolicitacao, PastaCliente
    empresas = get_empresas_filtradas(pessoa, request)
    cliente = get_object_or_404(Cliente, id=cliente_id, empresa__in=empresas)

    solicitacoes = Solicitacao.objects.filter(
        cliente=cliente
    ).select_related('empresa', 'criado_por', 'contato').order_by('-criado_em')

    pastas = PastaCliente.objects.filter(
        cliente=cliente, pasta_pai__isnull=True
    ).prefetch_related('arquivos_pasta', 'subpastas')

    context = {
        'pessoa': pessoa,
        'cliente': cliente,
        'solicitacoes': solicitacoes,
        'pendentes': solicitacoes.filter(status__in=['pendente', 'em_andamento']),
        'concluidas': solicitacoes.filter(status='concluido'),
        'tipos': TipoSolicitacao.choices,
        'empresas': empresas,
        'pastas': pastas,
    }
    return render(request, 'checklists/cliente_detalhe.html', context)


@login_required
@require_POST
def criar_solicitacao(request):
    """Cria nova solicitação ao cliente"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    from core.models import Solicitacao, NotificacaoInApp

    cliente_id = request.POST.get('cliente')
    titulo = request.POST.get('titulo', '').strip()
    descricao = request.POST.get('descricao', '').strip()
    tipo = request.POST.get('tipo', 'outro')
    prazo = request.POST.get('prazo') or None

    if not cliente_id or not titulo:
        messages.error(request, 'Cliente e título são obrigatórios.')
        return redirect('clientes_dashboard')

    empresas = get_empresas_filtradas(pessoa, request)
    cliente = get_object_or_404(Cliente, id=cliente_id, empresa__in=empresas)

    sol = Solicitacao.objects.create(
        empresa=cliente.empresa,
        cliente=cliente,
        criado_por=pessoa,
        titulo=titulo,
        descricao=descricao,
        tipo=tipo,
        prazo=prazo,
    )

    messages.success(request, f'Solicitação "{titulo}" criada para {cliente.nome}!')
    return redirect('cliente_detalhe', cliente_id=cliente.id)


@login_required
@require_POST
def solicitacao_status(request, sol_id):
    """Altera status de uma solicitação"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    from core.models import Solicitacao
    empresas = get_empresas_filtradas(pessoa, request)
    sol = get_object_or_404(Solicitacao, id=sol_id, empresa__in=empresas)

    novo_status = request.POST.get('status')
    if novo_status in ('pendente', 'em_andamento', 'concluido', 'cancelado'):
        sol.status = novo_status
        if novo_status == 'concluido':
            sol.concluido_em = timezone.now()
        sol.save()

    return redirect('cliente_detalhe', cliente_id=sol.cliente_id)


@login_required
@require_POST
def criar_cliente(request):
    """Cria empresa-cliente com contato principal"""
    from django.contrib.auth.models import User
    from core.models import ContatoCliente
    import secrets

    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    nome = request.POST.get('nome', '').strip()
    email = request.POST.get('email', '').strip()
    telefone = request.POST.get('telefone', '').strip()
    empresa_id = request.POST.get('empresa')
    cpf_cnpj = request.POST.get('cpf_cnpj', '').strip()
    segmento = request.POST.get('segmento', 'outro')
    tipo_contrato = request.POST.get('tipo_contrato', 'mensal')
    valor_mensal = request.POST.get('valor_mensal') or None
    dia_vencimento = request.POST.get('dia_vencimento') or None
    forma_pagamento = request.POST.get('forma_pagamento', 'boleto')
    data_inicio_contrato = request.POST.get('data_inicio_contrato') or None
    servicos = request.POST.get('servicos', '').strip()
    contato_nome = request.POST.get('contato_nome', '').strip()
    contato_email = request.POST.get('contato_email', '').strip()
    contato_telefone = request.POST.get('contato_telefone', '').strip()

    if not nome or not empresa_id or not contato_nome or not contato_email:
        messages.error(request, 'Nome da empresa, responsável e email são obrigatórios.')
        return redirect('clientes_dashboard')

    empresas = get_empresas_filtradas(pessoa, request)
    empresa = get_object_or_404(Empresa, id=empresa_id, id__in=empresas)

    cliente = Cliente.objects.create(
        empresa=empresa,
        nome=nome,
        razao_social=request.POST.get('razao_social', '').strip(),
        email=email,
        telefone=telefone,
        cpf_cnpj=cpf_cnpj,
        inscricao_estadual=request.POST.get('inscricao_estadual', '').strip(),
        inscricao_municipal=request.POST.get('inscricao_municipal', '').strip(),
        endereco=request.POST.get('endereco', '').strip(),
        cidade=request.POST.get('cidade', '').strip(),
        uf=request.POST.get('uf', '').strip().upper(),
        cep=request.POST.get('cep', '').strip(),
        site=request.POST.get('site', '').strip(),
        segmento=segmento,
        tipo_contrato=tipo_contrato,
        valor_mensal=valor_mensal,
        dia_vencimento=dia_vencimento,
        forma_pagamento=forma_pagamento,
        data_inicio_contrato=data_inicio_contrato,
        servicos=servicos,
    )

    # Criar user para o contato (login no portal)
    senha_temp = secrets.token_urlsafe(8)
    username = contato_email.split('@')[0]
    base_username = username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f'{base_username}{counter}'
        counter += 1

    user = User.objects.create_user(
        username=username,
        email=contato_email,
        password=senha_temp,
    )

    ContatoCliente.objects.create(
        cliente=cliente,
        user=user,
        nome=contato_nome,
        email=contato_email,
        telefone=contato_telefone,
        papel='dono',
    )

    messages.success(request, f'Cliente "{nome}" cadastrado! Responsável: {contato_nome} (senha: {senha_temp})')
    return redirect('cliente_detalhe', cliente_id=cliente.id)


@login_required
@require_POST
def editar_cliente(request, cliente_id):
    """Edita dados do cliente"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = get_empresas_filtradas(pessoa, request)
    cliente = get_object_or_404(Cliente, id=cliente_id, empresa__in=empresas)

    cliente.nome = request.POST.get('nome', cliente.nome).strip()
    cliente.razao_social = request.POST.get('razao_social', cliente.razao_social).strip()
    cliente.cpf_cnpj = request.POST.get('cpf_cnpj', cliente.cpf_cnpj).strip()
    cliente.inscricao_estadual = request.POST.get('inscricao_estadual', cliente.inscricao_estadual).strip()
    cliente.inscricao_municipal = request.POST.get('inscricao_municipal', cliente.inscricao_municipal).strip()
    cliente.email = request.POST.get('email', cliente.email).strip()
    cliente.telefone = request.POST.get('telefone', cliente.telefone).strip()
    cliente.site = request.POST.get('site', cliente.site).strip()
    cliente.endereco = request.POST.get('endereco', cliente.endereco).strip()
    cliente.cidade = request.POST.get('cidade', cliente.cidade).strip()
    cliente.uf = request.POST.get('uf', cliente.uf).strip().upper()
    cliente.cep = request.POST.get('cep', cliente.cep).strip()
    cliente.segmento = request.POST.get('segmento', cliente.segmento)
    cliente.status_contrato = request.POST.get('status_contrato', cliente.status_contrato)
    cliente.tipo_contrato = request.POST.get('tipo_contrato', cliente.tipo_contrato)
    cliente.forma_pagamento = request.POST.get('forma_pagamento', cliente.forma_pagamento)
    cliente.servicos = request.POST.get('servicos', cliente.servicos).strip()
    cliente.observacoes = request.POST.get('observacoes', cliente.observacoes).strip()

    valor = request.POST.get('valor_mensal')
    cliente.valor_mensal = valor if valor else None
    dia = request.POST.get('dia_vencimento')
    cliente.dia_vencimento = int(dia) if dia else None
    data_inicio = request.POST.get('data_inicio_contrato')
    cliente.data_inicio_contrato = data_inicio if data_inicio else None

    cliente.save()
    messages.success(request, f'Cliente "{cliente.nome}" atualizado!')
    return redirect('cliente_detalhe', cliente_id=cliente.id)


@login_required
@require_POST
def criar_contato_cliente(request, cliente_id):
    """Adiciona contato/funcionário a um cliente"""
    from django.contrib.auth.models import User
    from core.models import ContatoCliente
    import secrets

    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = get_empresas_filtradas(pessoa, request)
    cliente = get_object_or_404(Cliente, id=cliente_id, empresa__in=empresas)

    nome = request.POST.get('nome', '').strip()
    cpf = request.POST.get('cpf', '').strip()
    email = request.POST.get('email', '').strip()
    telefone = request.POST.get('telefone', '').strip()
    funcao = request.POST.get('funcao', '').strip()
    papel = request.POST.get('papel', 'funcionario')
    criar_acesso = 'criar_acesso' in request.POST

    if not nome or not email:
        messages.error(request, 'Nome e email são obrigatórios.')
        return redirect('cliente_detalhe', cliente_id=cliente.id)

    user = None
    senha_temp = ''
    if criar_acesso:
        senha_temp = secrets.token_urlsafe(8)
        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base_username}{counter}'
            counter += 1
        user = User.objects.create_user(username=username, email=email, password=senha_temp)

    ContatoCliente.objects.create(
        cliente=cliente, user=user, nome=nome, cpf=cpf, email=email,
        telefone=telefone, funcao=funcao, papel=papel,
    )

    msg = f'{nome} adicionado!'
    if senha_temp:
        msg += f' Senha portal: {senha_temp}'
    messages.success(request, msg)
    return redirect('cliente_detalhe', cliente_id=cliente.id)


@login_required
def config_pastas_empresa(request, empresa_id):
    """Configura templates de pastas para novos clientes de uma empresa"""
    from core.models import PastaTemplateEmpresa
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        return redirect('dashboard')

    empresa = get_object_or_404(Empresa, id=empresa_id)

    if request.method == 'POST':
        # Deletar e recriar
        PastaTemplateEmpresa.objects.filter(empresa=empresa).delete()
        pastas_json = request.POST.get('pastas_json', '[]')
        try:
            pastas = json.loads(pastas_json)
            for i, nome in enumerate(pastas):
                if nome.strip():
                    PastaTemplateEmpresa.objects.create(
                        empresa=empresa, nome=nome.strip(), ordem=i
                    )
        except (json.JSONDecodeError, TypeError):
            pass
        messages.success(request, f'Pastas padrão de {empresa.nome} atualizadas!')
        return redirect('clientes_dashboard')

    templates = list(PastaTemplateEmpresa.objects.filter(empresa=empresa).values_list('nome', flat=True))

    return render(request, 'checklists/config_pastas.html', {
        'empresa': empresa,
        'templates_json': json.dumps(templates) if templates else '["Materiais","Criativos","Documentos"]',
    })


@login_required
def pasta_detalhe_interno(request, pasta_id):
    """Página dedicada de pasta no painel interno"""
    from core.models import PastaCliente
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    pasta = get_object_or_404(PastaCliente, id=pasta_id)
    empresas = get_empresas_filtradas(pessoa, request)
    if pasta.cliente.empresa not in empresas:
        return redirect('dashboard')

    arquivos = pasta.arquivos_pasta.all().order_by('-criado_em')
    subpastas = PastaCliente.objects.filter(pasta_pai=pasta).order_by('nome')

    # Breadcrumb
    breadcrumb = []
    p = pasta
    while p:
        breadcrumb.insert(0, p)
        p = p.pasta_pai

    return render(request, 'checklists/pasta_detalhe.html', {
        'pessoa': pessoa,
        'pasta': pasta,
        'cliente': pasta.cliente,
        'arquivos': arquivos,
        'subpastas': subpastas,
        'breadcrumb': breadcrumb,
    })


@login_required
@require_POST
def criar_subpasta(request, pasta_id):
    """Cria subpasta dentro de uma pasta"""
    from core.models import PastaCliente
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    pasta_pai = get_object_or_404(PastaCliente, id=pasta_id)
    nome = request.POST.get('nome', '').strip()
    if nome:
        PastaCliente.objects.create(
            cliente=pasta_pai.cliente, nome=nome, pasta_pai=pasta_pai,
        )
    return redirect('pasta_detalhe_interno', pasta_id=pasta_pai.id)


@login_required
@require_POST
def upload_pasta(request, pasta_id):
    """Upload de arquivos em uma pasta do cliente"""
    from core.models import PastaCliente, ArquivoPasta
    pessoa = get_pessoa_or_redirect(request)
    pasta = get_object_or_404(PastaCliente, id=pasta_id)

    arquivos = request.FILES.getlist('arquivos')
    nome_enviador = pessoa.nome if pessoa else 'Equipe'

    for arq in arquivos:
        ArquivoPasta.objects.create(
            pasta=pasta, arquivo=arq, nome_original=arq.name,
            tamanho=arq.size, enviado_por=nome_enviador, enviado_por_cliente=False,
        )

    messages.success(request, f'{len(arquivos)} arquivo(s) enviado(s)!')
    return redirect('cliente_detalhe', cliente_id=pasta.cliente_id)


@login_required
@require_POST
def criar_pasta_cliente(request, cliente_id):
    """Cria nova pasta para um cliente"""
    from core.models import PastaCliente
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = get_empresas_filtradas(pessoa, request)
    cliente = get_object_or_404(Cliente, id=cliente_id, empresa__in=empresas)
    nome = request.POST.get('nome', '').strip()
    pasta_pai_id = request.POST.get('pasta_pai') or None

    if nome:
        PastaCliente.objects.create(
            cliente=cliente, nome=nome,
            pasta_pai_id=pasta_pai_id,
        )
        messages.success(request, f'Pasta "{nome}" criada!')

    return redirect('cliente_detalhe', cliente_id=cliente.id)


# ============================================
# PORTAL DO CLIENTE (acesso externo)
# ============================================

def portal_login(request):
    """Login do portal do cliente"""
    if request.method == 'POST':
        from django.contrib.auth import authenticate, login
        from core.models import ContatoCliente
        email = request.POST.get('email', '').strip()
        senha = request.POST.get('senha', '')
        user = authenticate(request, username=email, password=senha)
        if user and ContatoCliente.objects.filter(user=user).exists():
            login(request, user)
            return redirect('portal_home')
        messages.error(request, 'Email ou senha inválidos.')
    return render(request, 'portal/login.html')


@login_required
def portal_home(request):
    """Home do portal do cliente com dashboard"""
    from core.models import ContatoCliente, Solicitacao, PastaCliente

    contato = ContatoCliente.objects.filter(user=request.user).first()
    if not contato:
        return redirect('portal_login')

    cliente = contato.cliente
    pastas = PastaCliente.objects.filter(cliente=cliente, pasta_pai__isnull=True).order_by('nome')

    if contato.papel == 'dono':
        solicitacoes = Solicitacao.objects.filter(cliente=cliente)
    else:
        solicitacoes = Solicitacao.objects.filter(
            Q(cliente=cliente, contato__isnull=True) | Q(contato=contato)
        )

    solicitacoes = solicitacoes.exclude(status='cancelado').select_related('contato').prefetch_related('arquivos', 'comentarios')
    pendentes = solicitacoes.filter(status__in=['pendente', 'em_andamento']).order_by('prazo')
    concluidas = solicitacoes.filter(status='concluido').order_by('-concluido_em')

    # Dashboard stats
    atrasadas = [s for s in pendentes if s.esta_atrasada]
    vencendo_semana = [s for s in pendentes if not s.esta_atrasada and s.prazo and s.prazo <= timezone.now() + timedelta(days=7)]
    total_mes = solicitacoes.filter(criado_em__month=timezone.localdate().month).count()
    concluidas_mes = concluidas.filter(concluido_em__month=timezone.localdate().month).count()

    context = {
        'contato': contato,
        'cliente': cliente,
        'pendentes': pendentes,
        'concluidas': concluidas[:10],
        'total_pendentes': pendentes.count(),
        'atrasadas': len(atrasadas),
        'vencendo_semana': len(vencendo_semana),
        'total_mes': total_mes,
        'concluidas_mes': concluidas_mes,
        'pastas': pastas,
    }
    return render(request, 'portal/home.html', context)


@login_required
@require_POST
def portal_responder(request, sol_id):
    """Contato do cliente responde/conclui uma solicitação"""
    from core.models import ContatoCliente, Solicitacao, ArquivoSolicitacao

    contato = ContatoCliente.objects.filter(user=request.user).first()
    if not contato:
        return redirect('portal_login')

    from core.models import ComentarioSolicitacao

    sol = get_object_or_404(Solicitacao, id=sol_id, cliente=contato.cliente)

    # Comentário
    texto = request.POST.get('resposta', '').strip()
    if texto:
        ComentarioSolicitacao.objects.create(
            solicitacao=sol,
            autor_nome=contato.nome,
            autor_is_cliente=True,
            texto=texto,
        )

    # Upload múltiplo de arquivos com organização em pasta
    from core.models import PastaCliente, ArquivoPasta
    arquivos = request.FILES.getlist('arquivos')
    pasta_id = request.POST.get('pasta') or None
    pasta = None
    if pasta_id:
        pasta = PastaCliente.objects.filter(id=pasta_id, cliente=contato.cliente).first()

    for arq in arquivos:
        # Salvar na solicitação
        arq_sol = ArquivoSolicitacao.objects.create(
            solicitacao=sol,
            pasta=pasta,
            arquivo=arq,
            nome_original=arq.name,
            tamanho=arq.size,
            enviado_por_cliente=True,
            enviado_por_nome=contato.nome,
        )
        # Salvar também na pasta do Drive (se pasta selecionada)
        if pasta:
            ArquivoPasta.objects.create(
                pasta=pasta,
                arquivo=arq_sol.arquivo,
                nome_original=arq.name,
                tamanho=arq.size,
                enviado_por=contato.nome,
                enviado_por_cliente=True,
            )

    marcar_concluido = request.POST.get('concluir')
    if marcar_concluido:
        sol.status = 'concluido'
        sol.concluido_em = timezone.now()

    sol.save()
    messages.success(request, 'Enviado com sucesso!')
    return redirect('portal_home')


@login_required
@require_POST
def portal_upload_pasta(request, pasta_id):
    """Cliente faz upload em uma pasta"""
    from core.models import ContatoCliente, PastaCliente, ArquivoPasta

    contato = ContatoCliente.objects.filter(user=request.user).first()
    if not contato:
        return redirect('portal_login')

    pasta = get_object_or_404(PastaCliente, id=pasta_id, cliente=contato.cliente)

    arquivos = request.FILES.getlist('arquivos')
    for arq in arquivos:
        ArquivoPasta.objects.create(
            pasta=pasta, arquivo=arq, nome_original=arq.name,
            tamanho=arq.size, enviado_por=contato.nome, enviado_por_cliente=True,
        )

    messages.success(request, f'{len(arquivos)} arquivo(s) enviado(s)!')
    return redirect('portal_arquivos')


@login_required
def portal_arquivos(request):
    """Página de arquivos/pastas do cliente no portal"""
    from core.models import ContatoCliente, PastaCliente

    contato = ContatoCliente.objects.filter(user=request.user).first()
    if not contato:
        return redirect('portal_login')

    cliente = contato.cliente
    pastas = PastaCliente.objects.filter(cliente=cliente, pasta_pai__isnull=True).prefetch_related('arquivos_pasta')

    return render(request, 'portal/arquivos.html', {
        'contato': contato,
        'cliente': cliente,
        'pastas': pastas,
    })


@login_required
def portal_pasta_detalhe(request, pasta_id):
    """Página dedicada de uma pasta com preview de arquivos"""
    from core.models import ContatoCliente, PastaCliente

    contato = ContatoCliente.objects.filter(user=request.user).first()
    if not contato:
        return redirect('portal_login')

    pasta = get_object_or_404(PastaCliente, id=pasta_id, cliente=contato.cliente)
    arquivos = pasta.arquivos_pasta.all().order_by('-criado_em')

    return render(request, 'portal/pasta_detalhe.html', {
        'contato': contato,
        'cliente': contato.cliente,
        'pasta': pasta,
        'arquivos': arquivos,
    })


@login_required
@require_POST
def portal_criar_pasta(request):
    """Cliente cria uma subpasta"""
    from core.models import ContatoCliente, PastaCliente

    contato = ContatoCliente.objects.filter(user=request.user).first()
    if not contato:
        return redirect('portal_login')

    nome = request.POST.get('nome', '').strip()
    pasta_pai_id = request.POST.get('pasta_pai') or None

    if nome:
        PastaCliente.objects.create(
            cliente=contato.cliente, nome=nome,
            pasta_pai_id=pasta_pai_id, criada_por_cliente=True,
        )

    return redirect('portal_arquivos')


# ===========================================================
# DRIVE INTERNO (Arquivos da Empresa)
# ===========================================================

@login_required
def drive(request):
    """Drive de arquivos internos da empresa"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = get_empresas_filtradas(pessoa, request)
    empresa_id = request.GET.get('empresa', '')

    if empresa_id:
        empresa_selecionada = empresas.filter(id=empresa_id).first()
    elif empresas.count() == 1:
        empresa_selecionada = empresas.first()
    else:
        empresa_selecionada = None

    pastas = []
    if empresa_selecionada:
        pastas = PastaEmpresa.objects.filter(
            empresa=empresa_selecionada, pasta_pai__isnull=True
        ).prefetch_related('arquivos', 'subpastas').order_by('ordem', 'nome')

    context = {
        'pessoa': pessoa,
        'empresas': empresas,
        'empresa_selecionada': empresa_selecionada,
        'empresa_id': empresa_id,
        'pastas': pastas,
    }
    return render(request, 'checklists/drive.html', context)


@login_required
@require_POST
def drive_criar_pasta(request):
    """Cria uma nova pasta no Drive"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('drive')

    empresa_id = request.POST.get('empresa')
    nome = request.POST.get('nome', '').strip()
    pasta_pai_id = request.POST.get('pasta_pai') or None
    cor = request.POST.get('cor', '#f59e0b')

    empresas = get_empresas_filtradas(pessoa, request)
    empresa = empresas.filter(id=empresa_id).first()
    if not empresa or not nome:
        messages.error(request, 'Empresa e nome são obrigatórios.')
        return redirect('drive')

    PastaEmpresa.objects.create(
        empresa=empresa,
        nome=nome,
        pasta_pai_id=pasta_pai_id,
        criado_por=pessoa,
        cor=cor,
    )
    messages.success(request, f'Pasta "{nome}" criada!')
    return redirect(f'{request.META.get("HTTP_REFERER", "/drive/")}')


@login_required
@require_POST
def drive_upload(request, pasta_id):
    """Upload de arquivos para uma pasta do Drive"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('drive')

    empresas = get_empresas_filtradas(pessoa, request)
    pasta = get_object_or_404(PastaEmpresa, id=pasta_id, empresa__in=empresas)

    arquivos = request.FILES.getlist('arquivos')
    count = 0
    for arq in arquivos:
        if arq.size > 52428800:  # 50MB
            messages.warning(request, f'{arq.name} excede 50MB.')
            continue
        ArquivoEmpresa.objects.create(
            pasta=pasta,
            arquivo=arq,
            nome_original=arq.name,
            tamanho=arq.size,
            enviado_por=pessoa,
        )
        count += 1

    if count:
        messages.success(request, f'{count} arquivo(s) enviado(s)!')
    return redirect(request.META.get('HTTP_REFERER', '/drive/'))


@login_required
@require_POST
def drive_excluir_arquivo(request, arquivo_id):
    """Exclui um arquivo do Drive"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('drive')

    empresas = get_empresas_filtradas(pessoa, request)
    arq = get_object_or_404(ArquivoEmpresa, id=arquivo_id, pasta__empresa__in=empresas)
    nome = arq.nome_original
    arq.arquivo.delete(save=False)
    arq.delete()
    messages.success(request, f'Arquivo "{nome}" excluído.')
    return redirect(request.META.get('HTTP_REFERER', '/drive/'))


@login_required
@require_POST
def drive_excluir_pasta(request, pasta_id):
    """Exclui uma pasta e todos os arquivos"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        return redirect('drive')

    empresas = get_empresas_filtradas(pessoa, request)
    pasta = get_object_or_404(PastaEmpresa, id=pasta_id, empresa__in=empresas)
    nome = pasta.nome
    # Deletar arquivos do storage
    for arq in pasta.arquivos.all():
        arq.arquivo.delete(save=False)
    pasta.delete()
    messages.success(request, f'Pasta "{nome}" excluída.')
    return redirect(request.META.get('HTTP_REFERER', '/drive/'))


@login_required
@require_POST
def drive_renomear_pasta(request, pasta_id):
    """Renomeia uma pasta"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('drive')

    empresas = get_empresas_filtradas(pessoa, request)
    pasta = get_object_or_404(PastaEmpresa, id=pasta_id, empresa__in=empresas)
    novo_nome = request.POST.get('nome', '').strip()
    if novo_nome:
        pasta.nome = novo_nome
        pasta.save()
    return redirect(request.META.get('HTTP_REFERER', '/drive/'))
