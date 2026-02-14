import calendar
import logging
from datetime import date, timedelta
from decimal import Decimal

import requests
from django.utils import timezone

from .models import (
    CategoriaLancamento,
    ConfigMercadoPago,
    ContaPagar,
    ContaPagarItem,
    ContaReceber,
    ContaReceberItem,
    Lancamento,
    TipoLancamento,
)

logger = logging.getLogger(__name__)


# Mapeamento dia_execucao → weekday() do Python (0=segunda, 6=domingo)
_DIA_WEEKDAY = {
    'segunda': 0,
    'terca': 1,
    'quarta': 2,
    'quinta': 3,
    'sexta': 4,
    'sabado': 5,
}


def _calcular_data_execucao(data_vencimento, dia_execucao, dia_execucao_mensal=None):
    """Calcula a data de execução baseada no dia da semana ou dia do mês configurado.

    Se dia_execucao == 'mesmo_dia', retorna a própria data de vencimento.
    Se dia_execucao == 'dia_mes', retorna o dia específico do mês (dia_execucao_mensal).
    Caso contrário, retorna o dia da semana configurado que é <= data_vencimento
    (o dia da semana mais próximo antes ou no dia do vencimento).
    """
    if dia_execucao == 'mesmo_dia':
        return data_vencimento

    if dia_execucao == 'dia_mes' and dia_execucao_mensal:
        # Usar dia específico do mês
        ultimo_dia = calendar.monthrange(data_vencimento.year, data_vencimento.month)[1]
        dia = min(dia_execucao_mensal, ultimo_dia)  # Ajusta se mês tem menos dias
        return date(data_vencimento.year, data_vencimento.month, dia)

    weekday_alvo = _DIA_WEEKDAY.get(dia_execucao)
    if weekday_alvo is None:
        return data_vencimento

    # Encontrar o dia da semana alvo que é <= data_vencimento
    diff = (data_vencimento.weekday() - weekday_alvo) % 7
    data_exec = data_vencimento - timedelta(days=diff)
    return data_exec


def _deve_gerar_para_mes(conta, mes, ano):
    """Verifica se deve gerar item para este mês baseado na recorrência e data_vencimento."""
    recorrencia = conta.recorrencia

    # Usar data_vencimento como referência
    if conta.data_vencimento:
        mes_inicio = conta.data_vencimento.month
        ano_inicio = conta.data_vencimento.year
    else:
        # Fallback para criado_em (contas antigas)
        mes_inicio = conta.criado_em.month
        ano_inicio = conta.criado_em.year

    # Calcular diferença de meses desde o início
    meses_desde_inicio = (ano - ano_inicio) * 12 + (mes - mes_inicio)

    # Não gera para meses anteriores ao início
    if meses_desde_inicio < 0:
        return False

    # Conta única: só gera no mês/ano de início
    if recorrencia == 'unica':
        return meses_desde_inicio == 0

    # Diária: sempre gera (itens diários serão criados separadamente)
    if recorrencia == 'diaria':
        return True

    # Mensal, semanal, quinzenal: sempre gera a partir do início
    if recorrencia in ('mensal', 'semanal', 'quinzenal'):
        return True

    # Trimestral, semestral, anual
    if recorrencia == 'trimestral':
        return meses_desde_inicio % 3 == 0
    elif recorrencia == 'semestral':
        return meses_desde_inicio % 6 == 0
    elif recorrencia == 'anual':
        return meses_desde_inicio % 12 == 0

    return True


def gerar_parcelas_conta(conta):
    """Gera todas as parcelas de uma conta parcelada.

    Cria os ContaPagarItem para cada parcela, com vencimento mensal
    a partir da data de vencimento inicial.
    """
    if not conta.parcelado or conta.total_parcelas <= 1:
        return 0

    # Verificar se já existem parcelas
    if ContaPagarItem.objects.filter(conta_pagar=conta).exists():
        return 0

    data_venc = conta.data_vencimento
    criados = 0

    for parcela in range(1, conta.total_parcelas + 1):
        # Calcular data de vencimento da parcela
        # Primeira parcela: data_vencimento original
        # Próximas: mesmo dia nos meses seguintes
        if parcela == 1:
            venc = data_venc
        else:
            # Adicionar meses
            mes = data_venc.month + (parcela - 1)
            ano = data_venc.year
            while mes > 12:
                mes -= 12
                ano += 1
            # Ajustar dia se mês tem menos dias
            ultimo_dia = calendar.monthrange(ano, mes)[1]
            dia = min(data_venc.day, ultimo_dia)
            venc = date(ano, mes, dia)

        # Calcular data de execução
        data_execucao = _calcular_data_execucao(venc, conta.dia_execucao, conta.dia_execucao_mensal)

        ContaPagarItem.objects.create(
            conta_pagar=conta,
            mes=venc.month,
            ano=venc.year,
            valor=conta.valor,
            data_vencimento=venc,
            data_execucao=data_execucao,
            parcela_numero=parcela,
        )
        criados += 1

    return criados


def gerar_contas_pagar_mes(empresa, mes, ano):
    """Gera itens de contas a pagar para o mês especificado.

    Para cada ContaPagar ativa da empresa, cria um ContaPagarItem
    se ainda não existir para o mês/ano e se a recorrência permitir.
    """
    # Excluir contas parceladas (já têm itens gerados na criação)
    contas = ContaPagar.objects.filter(empresa=empresa, ativo=True).exclude(recorrencia='parcelada')
    criados = 0

    for conta in contas:
        # Verificar se já existe
        if ContaPagarItem.objects.filter(conta_pagar=conta, mes=mes, ano=ano).exists():
            continue

        # Verificar se deve gerar baseado na recorrência
        if not _deve_gerar_para_mes(conta, mes, ano):
            continue

        # Calcular data de vencimento
        ultimo_dia_mes = calendar.monthrange(ano, mes)[1]
        dia = min(conta.dia_vencimento, ultimo_dia_mes)
        data_vencimento = date(ano, mes, dia)

        # Calcular data de execução
        data_execucao = _calcular_data_execucao(data_vencimento, conta.dia_execucao, conta.dia_execucao_mensal)

        ContaPagarItem.objects.create(
            conta_pagar=conta,
            mes=mes,
            ano=ano,
            valor=conta.valor,
            data_vencimento=data_vencimento,
            data_execucao=data_execucao,
        )
        criados += 1

    return criados


def gerar_contas_pagar_todas_empresas():
    """Gera contas a pagar do mês atual para todas as empresas."""
    from core.models import Empresa
    hoje = timezone.localdate()
    total = 0
    for empresa in Empresa.objects.all():
        total += gerar_contas_pagar_mes(empresa, hoje.month, hoje.year)
    return total


# =====================================================
# CONTAS A RECEBER
# =====================================================

def _deve_gerar_receber_para_mes(conta, mes, ano):
    """Verifica se deve gerar item de recebimento para este mês baseado na recorrência."""
    recorrencia = conta.recorrencia

    # Usar data_vencimento como referência
    if conta.data_vencimento:
        mes_inicio = conta.data_vencimento.month
        ano_inicio = conta.data_vencimento.year
    else:
        mes_inicio = conta.criado_em.month
        ano_inicio = conta.criado_em.year

    meses_desde_inicio = (ano - ano_inicio) * 12 + (mes - mes_inicio)

    if meses_desde_inicio < 0:
        return False

    if recorrencia == 'unica':
        return meses_desde_inicio == 0

    if recorrencia in ('mensal', 'semanal', 'quinzenal'):
        return True

    if recorrencia == 'trimestral':
        return meses_desde_inicio % 3 == 0
    elif recorrencia == 'semestral':
        return meses_desde_inicio % 6 == 0
    elif recorrencia == 'anual':
        return meses_desde_inicio % 12 == 0

    return True


def gerar_parcelas_conta_receber(conta):
    """Gera todas as parcelas de uma conta a receber parcelada."""
    if not conta.parcelado or conta.total_parcelas <= 1:
        return 0

    if ContaReceberItem.objects.filter(conta_receber=conta).exists():
        return 0

    data_venc = conta.data_vencimento
    criados = 0

    for parcela in range(1, conta.total_parcelas + 1):
        if parcela == 1:
            venc = data_venc
        else:
            mes = data_venc.month + (parcela - 1)
            ano = data_venc.year
            while mes > 12:
                mes -= 12
                ano += 1
            ultimo_dia = calendar.monthrange(ano, mes)[1]
            dia = min(data_venc.day, ultimo_dia)
            venc = date(ano, mes, dia)

        ContaReceberItem.objects.create(
            conta_receber=conta,
            mes=venc.month,
            ano=venc.year,
            valor=conta.valor,
            data_vencimento=venc,
            parcela_numero=parcela,
        )
        criados += 1

    return criados


def gerar_contas_receber_mes(empresa, mes, ano):
    """Gera itens de contas a receber para o mês especificado."""
    contas = ContaReceber.objects.filter(empresa=empresa, ativo=True).exclude(recorrencia='parcelada')
    criados = 0

    for conta in contas:
        if ContaReceberItem.objects.filter(conta_receber=conta, mes=mes, ano=ano).exists():
            continue

        if not _deve_gerar_receber_para_mes(conta, mes, ano):
            continue

        ultimo_dia_mes = calendar.monthrange(ano, mes)[1]
        dia = min(conta.dia_vencimento, ultimo_dia_mes)
        data_vencimento = date(ano, mes, dia)

        ContaReceberItem.objects.create(
            conta_receber=conta,
            mes=mes,
            ano=ano,
            valor=conta.valor,
            data_vencimento=data_vencimento,
        )
        criados += 1

    return criados


def gerar_contas_receber_todas_empresas():
    """Gera contas a receber do mês atual para todas as empresas."""
    from core.models import Empresa
    hoje = timezone.localdate()
    total = 0
    for empresa in Empresa.objects.all():
        total += gerar_contas_receber_mes(empresa, hoje.month, hoje.year)
    return total


MP_API_BASE = 'https://api.mercadopago.com'


def _get_or_create_categorias(empresa):
    """Retorna dict com categorias MP, criando se necessário."""
    categorias = {}
    defaults = [
        ('Venda MP', TipoLancamento.ENTRADA, '#22c55e'),
        ('Taxa MP', TipoLancamento.SAIDA, '#6b7280'),
        ('Estorno MP', TipoLancamento.SAIDA, '#ef4444'),
    ]
    for nome, tipo, cor in defaults:
        cat, _ = CategoriaLancamento.objects.get_or_create(
            empresa=empresa, nome=nome, tipo=tipo,
            defaults={'cor': cor, 'ativo': True},
        )
        categorias[nome] = cat
    return categorias


def _fetch_payments(access_token, data_inicio, data_fim, offset=0):
    """Busca pagamentos aprovados na API do MP."""
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        'sort': 'date_approved',
        'criteria': 'asc',
        'begin_date': f'{data_inicio}T00:00:00.000-03:00',
        'end_date': f'{data_fim}T23:59:59.999-03:00',
        'status': 'approved',
        'offset': offset,
        'limit': 50,
    }
    resp = requests.get(
        f'{MP_API_BASE}/v1/payments/search',
        headers=headers,
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _fetch_refunds(access_token, payment_id):
    """Busca refunds de um pagamento."""
    headers = {'Authorization': f'Bearer {access_token}'}
    resp = requests.get(
        f'{MP_API_BASE}/v1/payments/{payment_id}/refunds',
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def sync_mercadopago(config: ConfigMercadoPago, data_inicio: date, data_fim: date):
    """
    Sincroniza pagamentos do Mercado Pago como lançamentos financeiros.
    Retorna dict com contadores: criados, taxas, estornos, ignorados.
    """
    empresa = config.empresa
    categorias = _get_or_create_categorias(empresa)
    stats = {'criados': 0, 'taxas': 0, 'estornos': 0, 'ignorados': 0, 'erros': []}

    offset = 0
    while True:
        data = _fetch_payments(config.access_token, data_inicio, data_fim, offset)
        results = data.get('results', [])
        if not results:
            break

        for payment in results:
            pid = str(payment['id'])
            mp_id_entrada = f'mp_{pid}'
            mp_id_taxa = f'mp_{pid}_fee'

            # Pular se já importado
            if Lancamento.objects.filter(mp_payment_id=mp_id_entrada).exists():
                stats['ignorados'] += 1
                continue

            # Data do pagamento
            date_approved = payment.get('date_approved', '')
            if date_approved:
                pay_date = date_approved[:10]
            else:
                pay_date = str(data_inicio)

            # Valor líquido recebido
            transaction_details = payment.get('transaction_details', {})
            net_amount = transaction_details.get('net_received_amount')
            gross_amount = payment.get('transaction_amount', 0)

            if net_amount is None:
                net_amount = gross_amount

            descricao = payment.get('description', '') or f'Pagamento MP #{pid}'
            external_ref = payment.get('external_reference', '')
            if external_ref:
                descricao = f'{descricao} (Ref: {external_ref})'

            # Lançamento de entrada (valor líquido)
            Lancamento.objects.create(
                empresa=empresa,
                tipo=TipoLancamento.ENTRADA,
                categoria=categorias['Venda MP'],
                descricao=descricao[:300],
                valor=Decimal(str(net_amount)),
                data=pay_date,
                mp_payment_id=mp_id_entrada,
                observacao=f'MP Payment ID: {pid}',
            )
            stats['criados'] += 1

            # Lançamento de taxa (se houver diferença)
            fee_amount = Decimal(str(gross_amount)) - Decimal(str(net_amount))
            if fee_amount > 0:
                if not Lancamento.objects.filter(mp_payment_id=mp_id_taxa).exists():
                    Lancamento.objects.create(
                        empresa=empresa,
                        tipo=TipoLancamento.SAIDA,
                        categoria=categorias['Taxa MP'],
                        descricao=f'Taxa MP - {descricao[:250]}',
                        valor=fee_amount,
                        data=pay_date,
                        mp_payment_id=mp_id_taxa,
                        observacao=f'Taxa sobre MP Payment ID: {pid}',
                    )
                    stats['taxas'] += 1

            # Buscar refunds
            try:
                refunds = _fetch_refunds(config.access_token, pid)
                for refund in refunds:
                    refund_id = str(refund.get('id', ''))
                    mp_id_refund = f'mp_{pid}_refund_{refund_id}'
                    if Lancamento.objects.filter(mp_payment_id=mp_id_refund).exists():
                        continue
                    refund_amount = refund.get('amount', 0)
                    if refund_amount > 0:
                        Lancamento.objects.create(
                            empresa=empresa,
                            tipo=TipoLancamento.SAIDA,
                            categoria=categorias['Estorno MP'],
                            descricao=f'Estorno MP - {descricao[:250]}',
                            valor=Decimal(str(refund_amount)),
                            data=pay_date,
                            mp_payment_id=mp_id_refund,
                            observacao=f'Refund {refund_id} do MP Payment ID: {pid}',
                        )
                        stats['estornos'] += 1
            except Exception as e:
                logger.warning(f'Erro ao buscar refunds do payment {pid}: {e}')
                stats['erros'].append(f'Refund {pid}: {e}')

        paging = data.get('paging', {})
        total = paging.get('total', 0)
        offset += len(results)
        if offset >= total:
            break

    config.ultima_sync = timezone.now()
    config.save(update_fields=['ultima_sync'])

    return stats
