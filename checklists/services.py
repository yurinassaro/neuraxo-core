"""
Serviço de geração automática de checklists baseado em recorrência
"""
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from .models import ChecklistTemplate, ChecklistItem, Recorrencia, StatusItem, SubTarefa
from core.models import Pessoa


def deve_gerar_hoje(template: ChecklistTemplate, data: date = None) -> bool:
    """Verifica se um template deve gerar item para a data especificada"""
    if data is None:
        data = timezone.localdate()

    recorrencia = template.recorrencia

    if recorrencia == Recorrencia.DIARIA:
        if template.dias_semana_ativos:
            dias = [int(d.strip()) for d in template.dias_semana_ativos.split(',') if d.strip().isdigit()]
            return data.weekday() in dias
        return True

    elif recorrencia == Recorrencia.SEMANAL:
        # Gera no dia da semana configurado (default: segunda = 0)
        dia = template.dia_semana if template.dia_semana is not None else 0
        return data.weekday() == dia

    elif recorrencia == Recorrencia.QUINZENAL:
        # Gera nos dias 1 e 15 de cada mês
        return data.day in [1, 15]

    elif recorrencia == Recorrencia.MENSAL:
        # Gera no dia configurado (default: dia 1)
        dia = template.dia_mes if template.dia_mes else 1
        # Se o mês não tem esse dia, usa o último dia do mês
        ultimo_dia = (data.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        dia_efetivo = min(dia, ultimo_dia.day)
        return data.day == dia_efetivo

    elif recorrencia == Recorrencia.TRIMESTRAL:
        # Gera em Jan, Abr, Jul, Out (dia 1)
        dia = template.dia_mes if template.dia_mes else 1
        return data.month in [1, 4, 7, 10] and data.day == dia

    elif recorrencia == Recorrencia.SEMESTRAL:
        # Gera em Jan e Jul (dia 1)
        dia = template.dia_mes if template.dia_mes else 1
        return data.month in [1, 7] and data.day == dia

    elif recorrencia == Recorrencia.ANUAL:
        # Gera em Janeiro (dia 1)
        dia = template.dia_mes if template.dia_mes else 1
        return data.month == 1 and data.day == dia

    return False


def obter_responsaveis(template: ChecklistTemplate) -> list:
    """Retorna lista de pessoas responsáveis pelo template"""
    if template.responsavel:
        return [template.responsavel] if template.responsavel.ativo else []

    if template.cargo_responsavel:
        return list(Pessoa.objects.filter(
            cargo=template.cargo_responsavel,
            ativo=True,
            empresas=template.empresa
        ))

    # Se não tem responsável específico, retorna todas as pessoas ativas do empresa
    return list(template.empresa.pessoas.filter(ativo=True))


def calcular_data_limite(template: ChecklistTemplate, data_referencia: date) -> datetime:
    """Calcula a data limite baseada na recorrência"""
    # Por padrão, deadline é fim do dia (23:59)
    hora_limite = datetime.combine(data_referencia, datetime.max.time().replace(microsecond=0))

    recorrencia = template.recorrencia

    if recorrencia == Recorrencia.DIARIA:
        # Deadline: fim do mesmo dia
        pass

    elif recorrencia == Recorrencia.SEMANAL:
        # Deadline: fim da semana (domingo)
        dias_ate_domingo = 6 - data_referencia.weekday()
        hora_limite = datetime.combine(data_referencia + timedelta(days=dias_ate_domingo),
                                        datetime.max.time().replace(microsecond=0))

    elif recorrencia == Recorrencia.QUINZENAL:
        # Deadline: dia 14 ou último dia do mês
        if data_referencia.day == 1:
            hora_limite = datetime.combine(data_referencia.replace(day=14),
                                            datetime.max.time().replace(microsecond=0))
        else:
            ultimo_dia = (data_referencia.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            hora_limite = datetime.combine(ultimo_dia, datetime.max.time().replace(microsecond=0))

    elif recorrencia == Recorrencia.MENSAL:
        # Deadline: último dia do mês
        ultimo_dia = (data_referencia.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        hora_limite = datetime.combine(ultimo_dia, datetime.max.time().replace(microsecond=0))

    elif recorrencia == Recorrencia.TRIMESTRAL:
        # Deadline: último dia do trimestre
        mes_fim_trimestre = ((data_referencia.month - 1) // 3 + 1) * 3
        ultimo_dia_trimestre = date(data_referencia.year, mes_fim_trimestre, 1) + timedelta(days=32)
        ultimo_dia_trimestre = ultimo_dia_trimestre.replace(day=1) - timedelta(days=1)
        hora_limite = datetime.combine(ultimo_dia_trimestre, datetime.max.time().replace(microsecond=0))

    elif recorrencia == Recorrencia.SEMESTRAL:
        # Deadline: fim de Jun ou Dez
        mes_fim = 6 if data_referencia.month <= 6 else 12
        dia_fim = 30 if mes_fim == 6 else 31
        hora_limite = datetime.combine(date(data_referencia.year, mes_fim, dia_fim),
                                        datetime.max.time().replace(microsecond=0))

    elif recorrencia == Recorrencia.ANUAL:
        # Deadline: fim do ano
        hora_limite = datetime.combine(date(data_referencia.year, 12, 31),
                                        datetime.max.time().replace(microsecond=0))

    return timezone.make_aware(hora_limite)


def gerar_checklists_do_dia(data: date = None) -> dict:
    """Gera todos os checklists do dia"""
    if data is None:
        data = timezone.localdate()

    resultado = {
        'data': data,
        'gerados': 0,
        'ignorados': 0,
        'erros': []
    }

    templates = ChecklistTemplate.objects.filter(ativo=True).select_related(
        'empresa', 'responsavel', 'cargo_responsavel'
    )

    for template in templates:
        if not deve_gerar_hoje(template, data):
            continue

        responsaveis = obter_responsaveis(template)
        if not responsaveis:
            resultado['erros'].append(f"Template '{template.titulo}' sem responsáveis")
            continue

        data_limite = calcular_data_limite(template, data)

        for pessoa in responsaveis:
            # Verifica se já existe
            existe = ChecklistItem.objects.filter(
                template=template,
                responsavel=pessoa,
                data_referencia=data
            ).exists()

            if existe:
                resultado['ignorados'] += 1
                continue

            item = ChecklistItem.objects.create(
                template=template,
                responsavel=pessoa,
                data_referencia=data,
                data_limite=data_limite,
                descricao=template.descricao,
                processo=template.processo,
            )
            # Copiar subtarefas do template
            for st in template.subtarefas_template.all():
                SubTarefa.objects.create(
                    checklist_item=item,
                    titulo=st.titulo,
                    ordem=st.ordem,
                )
            resultado['gerados'] += 1

    return resultado


def atualizar_status_atrasados():
    """Atualiza status de itens atrasados"""
    agora = timezone.now()
    itens_atrasados = ChecklistItem.objects.filter(
        status__in=[StatusItem.PENDENTE, StatusItem.EM_ANDAMENTO],
        data_limite__lt=agora
    )
    count = itens_atrasados.update(status=StatusItem.ATRASADO)
    return count


def obter_resumo_pessoa(pessoa: Pessoa, data: date = None) -> dict:
    """Retorna resumo das tarefas de uma pessoa"""
    if data is None:
        data = timezone.localdate()

    items = ChecklistItem.objects.filter(
        responsavel=pessoa,
        data_referencia=data
    ).select_related('template', 'template__empresa')

    return {
        'pessoa': pessoa,
        'data': data,
        'total': items.count(),
        'pendentes': items.filter(status=StatusItem.PENDENTE).count(),
        'em_andamento': items.filter(status=StatusItem.EM_ANDAMENTO).count(),
        'concluidos': items.filter(status=StatusItem.CONCLUIDO).count(),
        'atrasados': items.filter(status=StatusItem.ATRASADO).count(),
        'items': list(items)
    }
