from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum, Q, F, Value, CharField
from django.db.models.functions import Coalesce
from .models import MetaEmpresa, CategoriaLancamento, Lancamento, TipoLancamento, ConfigMercadoPago, ContaBancaria, PrestacaoConta, ContaPagar, ContaPagarItem, ContaReceber, ContaReceberItem, AlertaFinanceiro, HistoricoAlerta
from core.models import Pessoa, Empresa
from checklists.models import Projeto
from decimal import Decimal
import json
from datetime import datetime, timedelta


def get_pessoa_or_redirect(request):
    try:
        return request.user.pessoa
    except Pessoa.DoesNotExist:
        return None


@login_required
def dashboard_financeiro(request):
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    hoje = timezone.localdate()
    empresas = Empresa.objects.all()
    empresa_id = request.GET.get('empresa')

    if empresa_id:
        empresa = get_object_or_404(Empresa, id=empresa_id)
    elif empresas.exists():
        empresa = empresas.first()
    else:
        return render(request, 'financeiro/dashboard.html', {'empresas': empresas})

    # Meta do mês atual
    meta = MetaEmpresa.objects.filter(empresa=empresa, mes=hoje.month, ano=hoje.year).first()

    # Lançamentos do dia
    lancamentos_hoje = Lancamento.objects.filter(empresa=empresa, data=hoje).select_related('categoria', 'pessoa', 'projeto')
    entradas_hoje = lancamentos_hoje.filter(tipo='entrada').aggregate(t=Sum('valor'))['t'] or Decimal('0')
    saidas_hoje = lancamentos_hoje.filter(tipo='saida').aggregate(t=Sum('valor'))['t'] or Decimal('0')
    saldo_hoje = entradas_hoje - saidas_hoje

    # Lançamentos do mês
    lancamentos_mes = Lancamento.objects.filter(empresa=empresa, data__month=hoje.month, data__year=hoje.year)
    entradas_mes = lancamentos_mes.filter(tipo='entrada').aggregate(t=Sum('valor'))['t'] or Decimal('0')
    saidas_mes = lancamentos_mes.filter(tipo='saida').aggregate(t=Sum('valor'))['t'] or Decimal('0')
    saldo_mes = entradas_mes - saidas_mes

    # Últimos 10 lançamentos
    ultimos = Lancamento.objects.filter(empresa=empresa).select_related('categoria', 'pessoa', 'projeto')[:10]

    # Gastos por categoria (mês)
    categorias_saida = lancamentos_mes.filter(tipo='saida').values('categoria__nome', 'categoria__cor').annotate(
        total=Sum('valor')).order_by('-total')
    categorias_entrada = lancamentos_mes.filter(tipo='entrada').values('categoria__nome', 'categoria__cor').annotate(
        total=Sum('valor')).order_by('-total')

    context = {
        'empresas': empresas,
        'empresa': empresa,
        'meta': meta,
        'lancamentos_hoje': lancamentos_hoje,
        'entradas_hoje': entradas_hoje,
        'saidas_hoje': saidas_hoje,
        'saldo_hoje': saldo_hoje,
        'entradas_mes': entradas_mes,
        'saidas_mes': saidas_mes,
        'saldo_mes': saldo_mes,
        'ultimos': ultimos,
        'categorias_saida': categorias_saida,
        'categorias_entrada': categorias_entrada,
        'hoje': hoje,
    }
    return render(request, 'financeiro/dashboard.html', context)


@login_required
def lancar(request):
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = Empresa.objects.all()
    empresa_id = request.GET.get('empresa') or request.POST.get('empresa')
    empresa = None
    categorias = []

    if empresa_id:
        empresa = get_object_or_404(Empresa, id=empresa_id)
        categorias = CategoriaLancamento.objects.filter(
            Q(empresa=empresa) | Q(empresa__isnull=True), ativo=True
        ).order_by('tipo', 'ordem', 'nome')

    projetos = Projeto.objects.filter(empresa_id=empresa_id) if empresa_id else []
    pessoas = Pessoa.objects.filter(empresas__id=empresa_id) if empresa_id else []

    if request.method == 'POST':
        empresa_post_id = request.POST.get('empresa')
        if not empresa_post_id:
            messages.error(request, 'Selecione uma empresa.')
            return redirect('lancar')
        empresa = get_object_or_404(Empresa, id=empresa_post_id)
        tipo = request.POST.get('tipo')
        categoria_id = request.POST.get('categoria') or None
        descricao = request.POST.get('descricao', '').strip()
        valor = request.POST.get('valor', '0').replace(',', '.')
        data = request.POST.get('data') or timezone.localdate()
        pessoa_id = request.POST.get('pessoa') or None
        projeto_id = request.POST.get('projeto') or None
        observacao = request.POST.get('observacao', '').strip()

        try:
            valor = Decimal(valor)
        except Exception:
            messages.error(request, 'Valor inválido.')
            return redirect('lancar')

        if not descricao:
            messages.error(request, 'Descrição obrigatória.')
            return redirect('lancar')

        Lancamento.objects.create(
            empresa=empresa,
            tipo=tipo,
            categoria_id=categoria_id,
            descricao=descricao,
            valor=valor,
            data=data,
            pessoa_id=pessoa_id,
            projeto_id=projeto_id,
            observacao=observacao,
            criado_por=pessoa,
        )
        messages.success(request, f'Lançamento de R$ {valor:,.2f} registrado.')
        return redirect('dashboard_financeiro')

    context = {
        'empresas': empresas,
        'empresa': empresa,
        'categorias': categorias,
        'projetos': projetos,
        'pessoas': pessoas,
        'tipos': TipoLancamento.choices,
    }
    return render(request, 'financeiro/lancar.html', context)


@login_required
def lista_lancamentos(request):
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = Empresa.objects.all()
    empresa_id = request.GET.get('empresa')
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    tipo = request.GET.get('tipo')
    hoje = timezone.localdate()

    lancamentos = Lancamento.objects.select_related('empresa', 'categoria', 'pessoa', 'projeto')

    if empresa_id:
        lancamentos = lancamentos.filter(empresa_id=empresa_id)
    if not mes:
        mes = hoje.month
    if not ano:
        ano = hoje.year
    lancamentos = lancamentos.filter(data__month=int(mes), data__year=int(ano))
    if tipo:
        lancamentos = lancamentos.filter(tipo=tipo)

    total_entradas = lancamentos.filter(tipo='entrada').aggregate(t=Sum('valor'))['t'] or Decimal('0')
    total_saidas = lancamentos.filter(tipo='saida').aggregate(t=Sum('valor'))['t'] or Decimal('0')

    # Categorias para ação em lote
    categorias = CategoriaLancamento.objects.filter(ativo=True)
    if empresa_id:
        categorias = categorias.filter(Q(empresa_id=empresa_id) | Q(empresa__isnull=True))
    categorias = categorias.order_by('tipo', 'ordem', 'nome')

    sem_categoria = request.GET.get('sem_categoria')

    lancamentos_qs = lancamentos
    if sem_categoria:
        lancamentos_qs = lancamentos_qs.filter(categoria__isnull=True)

    context = {
        'lancamentos': lancamentos_qs[:500],
        'empresas': empresas,
        'empresa_id': empresa_id,
        'mes': int(mes),
        'ano': int(ano),
        'tipo': tipo,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'saldo': total_entradas - total_saidas,
        'categorias': categorias,
        'sem_categoria': sem_categoria,
    }
    return render(request, 'financeiro/lista_lancamentos.html', context)


@login_required
@require_POST
def categorizar_lote(request):
    """Categoriza vários lançamentos de uma vez."""
    categoria_id = request.POST.get('categoria_id')
    ids = request.POST.getlist('lancamento_ids')

    if not ids:
        messages.warning(request, 'Nenhum lançamento selecionado.')
        return redirect(request.META.get('HTTP_REFERER', 'lista_lancamentos'))

    if not categoria_id:
        messages.error(request, 'Selecione uma categoria.')
        return redirect(request.META.get('HTTP_REFERER', 'lista_lancamentos'))

    categoria = get_object_or_404(CategoriaLancamento, id=categoria_id)
    qtd = Lancamento.objects.filter(id__in=ids).update(categoria=categoria)
    messages.success(request, f'{qtd} lançamentos categorizados como "{categoria.nome}".')
    return redirect(request.META.get('HTTP_REFERER', 'lista_lancamentos'))


@login_required
@require_POST
def excluir_lancamento(request, lancamento_id):
    lancamento = get_object_or_404(Lancamento, id=lancamento_id)
    lancamento.delete()
    messages.success(request, 'Lançamento excluído.')
    return redirect('lista_lancamentos')


@login_required
def gerenciar_metas(request):
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = Empresa.objects.all()
    hoje = timezone.localdate()

    if request.method == 'POST':
        empresa = get_object_or_404(Empresa, id=request.POST.get('empresa'))
        mes = int(request.POST.get('mes'))
        ano = int(request.POST.get('ano'))
        valor_meta = Decimal(request.POST.get('valor_meta', '0').replace(',', '.'))
        dias_uteis = int(request.POST.get('dias_uteis', 22))

        meta, created = MetaEmpresa.objects.update_or_create(
            empresa=empresa, mes=mes, ano=ano,
            defaults={'valor_meta': valor_meta, 'dias_uteis': dias_uteis}
        )
        action = 'criada' if created else 'atualizada'
        messages.success(request, f'Meta {action}: R$ {valor_meta:,.2f} para {mes:02d}/{ano}')
        return redirect('gerenciar_metas')

    metas = MetaEmpresa.objects.select_related('empresa').order_by('-ano', '-mes')[:24]

    context = {
        'empresas': empresas,
        'metas': metas,
        'hoje': hoje,
        'meses': list(range(1, 13)),
    }
    return render(request, 'financeiro/metas.html', context)


@login_required
def gerenciar_categorias(request):
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = Empresa.objects.all()

    if request.method == 'POST':
        empresa_id = request.POST.get('empresa') or None
        nome = request.POST.get('nome', '').strip()
        tipo = request.POST.get('tipo')
        cor = request.POST.get('cor', '#6b7280')

        if nome and tipo:
            CategoriaLancamento.objects.create(
                empresa_id=empresa_id,
                nome=nome,
                tipo=tipo,
                cor=cor,
            )
            messages.success(request, f'Categoria "{nome}" criada.')
        return redirect('gerenciar_categorias')

    categorias = CategoriaLancamento.objects.select_related('empresa').order_by('tipo', 'ordem', 'nome')

    context = {
        'empresas': empresas,
        'categorias': categorias,
        'tipos': TipoLancamento.choices,
    }
    return render(request, 'financeiro/categorias.html', context)


@login_required
def categorias_por_empresa(request, empresa_id):
    categorias = CategoriaLancamento.objects.filter(
        Q(empresa_id=empresa_id) | Q(empresa__isnull=True), ativo=True
    ).order_by('tipo', 'ordem', 'nome')
    data = [{'id': c.id, 'nome': c.nome, 'tipo': c.tipo} for c in categorias]
    return JsonResponse(data, safe=False)


@login_required
def config_mercadopago(request):
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = Empresa.objects.all()

    if request.method == 'POST':
        empresa = get_object_or_404(Empresa, id=request.POST.get('empresa'))
        access_token = request.POST.get('access_token', '').strip()
        ativo = request.POST.get('ativo') == 'on'

        if not access_token:
            messages.error(request, 'Access Token obrigatório.')
            return redirect('config_mercadopago')

        config, created = ConfigMercadoPago.objects.update_or_create(
            empresa=empresa,
            defaults={'access_token': access_token, 'ativo': ativo},
        )
        action = 'configurada' if created else 'atualizada'
        messages.success(request, f'Integração MP {action} para {empresa.nome}.')
        return redirect('config_mercadopago')

    configs = ConfigMercadoPago.objects.select_related('empresa').all()
    context = {
        'empresas': empresas,
        'configs': configs,
    }
    return render(request, 'financeiro/mercadopago.html', context)


@login_required
@require_POST
def sync_mercadopago_view(request):
    from .services import sync_mercadopago

    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresa = get_object_or_404(Empresa, id=request.POST.get('empresa'))
    try:
        config = ConfigMercadoPago.objects.get(empresa=empresa, ativo=True)
    except ConfigMercadoPago.DoesNotExist:
        messages.error(request, f'Nenhuma configuração MP ativa para {empresa.nome}.')
        return redirect('config_mercadopago')

    data_inicio = request.POST.get('data_inicio')
    data_fim = request.POST.get('data_fim')

    if not data_inicio or not data_fim:
        messages.error(request, 'Informe data início e data fim.')
        return redirect('config_mercadopago')

    try:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Formato de data inválido.')
        return redirect('config_mercadopago')

    try:
        stats = sync_mercadopago(config, data_inicio, data_fim)
        messages.success(
            request,
            f'Sync {empresa.nome}: {stats["criados"]} vendas, '
            f'{stats["taxas"]} taxas, {stats["estornos"]} estornos importados. '
            f'{stats["ignorados"]} já existentes.'
        )
        if stats['erros']:
            messages.warning(request, f'Avisos: {"; ".join(stats["erros"][:3])}')
    except Exception as e:
        messages.error(request, f'Erro na sincronização: {e}')

    return redirect('config_mercadopago')


@login_required
def contas_bancarias(request):
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = Empresa.objects.all()

    if request.method == 'POST':
        empresa = get_object_or_404(Empresa, id=request.POST.get('empresa'))
        nome = request.POST.get('nome', '').strip()
        banco = request.POST.get('banco', '').strip()
        tipo_conta = request.POST.get('tipo_conta', 'corrente')
        agencia = request.POST.get('agencia', '').strip()
        numero_conta = request.POST.get('numero_conta', '').strip()
        saldo_inicial = request.POST.get('saldo_inicial', '0').replace(',', '.')
        cor = request.POST.get('cor', '#3b82f6')

        if not nome:
            messages.error(request, 'Nome da conta obrigatório.')
            return redirect('contas_bancarias')

        try:
            saldo_inicial = Decimal(saldo_inicial)
        except Exception:
            saldo_inicial = Decimal('0')

        ContaBancaria.objects.create(
            empresa=empresa, nome=nome, banco=banco, tipo_conta=tipo_conta,
            agencia=agencia, numero_conta=numero_conta,
            saldo_inicial=saldo_inicial, cor=cor,
        )
        messages.success(request, f'Conta "{nome}" criada.')
        return redirect('contas_bancarias')

    contas = ContaBancaria.objects.filter(ativo=True).select_related('empresa')
    context = {
        'empresas': empresas,
        'contas': contas,
        'tipos_conta': ContaBancaria.TIPO_CONTA_CHOICES,
    }
    return render(request, 'financeiro/contas_bancarias.html', context)


@login_required
def importar_extrato(request):
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    contas = ContaBancaria.objects.filter(ativo=True).select_related('empresa')

    if request.method == 'POST':
        from .extrato import parse_extrato

        conta_id = request.POST.get('conta')
        arquivo = request.FILES.get('arquivo')

        if not conta_id or not arquivo:
            messages.error(request, 'Selecione a conta e o arquivo.')
            return redirect('importar_extrato')

        conta = get_object_or_404(ContaBancaria, id=conta_id, ativo=True)

        try:
            lancamentos_parsed = parse_extrato(arquivo, arquivo.name)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('importar_extrato')
        except Exception as e:
            messages.error(request, f'Erro ao processar arquivo: {e}')
            return redirect('importar_extrato')

        if not lancamentos_parsed:
            messages.warning(request, 'Nenhum lançamento encontrado no arquivo. Verifique o formato.')
            return redirect('importar_extrato')

        # Preview mode
        if 'preview' in request.POST:
            context = {
                'contas': contas,
                'conta': conta,
                'lancamentos_parsed': lancamentos_parsed,
                'total_entradas': sum(l['valor'] for l in lancamentos_parsed if l['valor'] > 0),
                'total_saidas': sum(abs(l['valor']) for l in lancamentos_parsed if l['valor'] < 0),
                'arquivo_nome': arquivo.name,
            }
            return render(request, 'financeiro/importar_extrato.html', context)

        # Importação
        criados = 0
        for item in lancamentos_parsed:
            if item['valor'] > 0:
                tipo = 'entrada'
                valor = item['valor']
            else:
                tipo = 'saida'
                valor = abs(item['valor'])

            Lancamento.objects.create(
                empresa=conta.empresa,
                conta=conta,
                tipo=tipo,
                descricao=item['descricao'],
                valor=valor,
                data=item['data'],
                observacao=f'Importado do extrato: {arquivo.name}',
                criado_por=pessoa,
            )
            criados += 1

        messages.success(request, f'{criados} lançamentos importados para {conta.nome}.')
        return redirect('contas_bancarias')

    context = {'contas': contas}
    return render(request, 'financeiro/importar_extrato.html', context)


@login_required
def prestacao_contas(request, lancamento_id):
    """Detalhar gastos empresariais pagos com dinheiro de uma retirada."""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    lancamento = get_object_or_404(Lancamento, id=lancamento_id)
    categorias = CategoriaLancamento.objects.filter(
        Q(empresa=lancamento.empresa) | Q(empresa__isnull=True), ativo=True
    ).order_by('tipo', 'ordem', 'nome')

    if request.method == 'POST':
        descricao = request.POST.get('descricao', '').strip()
        valor = request.POST.get('valor', '0').replace(',', '.')
        categoria_id = request.POST.get('categoria') or None

        try:
            valor = Decimal(valor)
        except Exception:
            messages.error(request, 'Valor inválido.')
            return redirect('prestacao_contas', lancamento_id=lancamento_id)

        if not descricao:
            messages.error(request, 'Descrição obrigatória.')
            return redirect('prestacao_contas', lancamento_id=lancamento_id)

        if valor > lancamento.retirada_liquida:
            messages.error(request, f'Valor excede a retirada líquida (R$ {lancamento.retirada_liquida:.2f}).')
            return redirect('prestacao_contas', lancamento_id=lancamento_id)

        PrestacaoConta.objects.create(
            lancamento=lancamento,
            descricao=descricao,
            categoria_id=categoria_id,
            valor=valor,
        )
        messages.success(request, f'Prestação de R$ {valor:,.2f} registrada.')
        return redirect('prestacao_contas', lancamento_id=lancamento_id)

    prestacoes = lancamento.prestacoes.select_related('categoria').all()

    context = {
        'lancamento': lancamento,
        'prestacoes': prestacoes,
        'categorias': categorias,
    }
    return render(request, 'financeiro/prestacao_contas.html', context)


@login_required
@require_POST
def excluir_prestacao(request, prestacao_id):
    prestacao = get_object_or_404(PrestacaoConta, id=prestacao_id)
    lancamento_id = prestacao.lancamento_id
    prestacao.delete()
    messages.success(request, 'Prestação excluída.')
    return redirect('prestacao_contas', lancamento_id=lancamento_id)


@login_required
def relatorio_financeiro(request):
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = Empresa.objects.all()
    hoje = timezone.localdate()
    empresa_id = request.GET.get('empresa')
    mes = int(request.GET.get('mes', hoje.month))
    ano = int(request.GET.get('ano', hoje.year))

    if empresa_id:
        empresa = get_object_or_404(Empresa, id=empresa_id)
    elif empresas.exists():
        empresa = empresas.first()
    else:
        return render(request, 'financeiro/relatorio.html', {'empresas': empresas})

    lancamentos = Lancamento.objects.filter(
        empresa=empresa, data__month=mes, data__year=ano
    ).select_related('categoria')

    # --- Totais gerais ---
    total_entradas = lancamentos.filter(tipo='entrada').aggregate(t=Sum('valor'))['t'] or Decimal('0')
    total_saidas = lancamentos.filter(tipo='saida').aggregate(t=Sum('valor'))['t'] or Decimal('0')
    lucro_bruto = total_entradas - total_saidas

    # --- Por categoria (entradas) ---
    cat_entradas = lancamentos.filter(tipo='entrada').values(
        'categoria__nome', 'categoria__cor'
    ).annotate(total=Sum('valor'), qtd=Sum(Value(1))).order_by('-total')

    # --- Por categoria (saídas) ---
    cat_saidas = lancamentos.filter(tipo='saida').values(
        'categoria__nome', 'categoria__cor'
    ).annotate(total=Sum('valor'), qtd=Sum(Value(1))).order_by('-total')

    # --- Retiradas sócios ---
    retirada_renan = lancamentos.filter(
        tipo='saida', categoria__nome='Retirada Renan'
    ).aggregate(t=Sum('valor'))['t'] or Decimal('0')

    retirada_yuri = lancamentos.filter(
        tipo='saida', categoria__nome='Retirada Yuri'
    ).aggregate(t=Sum('valor'))['t'] or Decimal('0')

    # Prestações de conta (gastos empresa pagos pelo Renan)
    prestacoes_renan = PrestacaoConta.objects.filter(
        lancamento__empresa=empresa,
        lancamento__data__month=mes,
        lancamento__data__year=ano,
        lancamento__categoria__nome='Retirada Renan',
    ).aggregate(t=Sum('valor'))['t'] or Decimal('0')

    retirada_renan_liquida = retirada_renan - prestacoes_renan

    # --- Custos operacionais (saídas que não são retirada) ---
    custos_operacionais = lancamentos.filter(tipo='saida').exclude(
        categoria__nome__in=['Retirada Renan', 'Retirada Yuri']
    ).aggregate(t=Sum('valor'))['t'] or Decimal('0')

    # Gastos empresa pagos pelo Renan (prestações)
    custos_operacionais_total = custos_operacionais + prestacoes_renan

    # --- Lucro líquido (receita - custos operacionais reais) ---
    lucro_liquido = total_entradas - custos_operacionais_total

    # --- Divisão 50/50 ---
    direito_cada = lucro_liquido / 2 if lucro_liquido > 0 else Decimal('0')
    saldo_yuri = direito_cada - retirada_yuri  # quanto Yuri ainda tem pra tirar
    saldo_renan = direito_cada - retirada_renan_liquida  # quanto Renan ainda tem pra tirar

    # --- Prestações detalhadas ---
    prestacoes_detalhe = PrestacaoConta.objects.filter(
        lancamento__empresa=empresa,
        lancamento__data__month=mes,
        lancamento__data__year=ano,
    ).select_related('categoria', 'lancamento')

    # --- Detalhe retiradas Yuri ---
    retiradas_yuri_detalhe = lancamentos.filter(
        tipo='saida', categoria__nome='Retirada Yuri'
    ).order_by('data')

    # --- Meses com dados (para navegação) ---
    meses_disponiveis = Lancamento.objects.filter(empresa=empresa).dates('data', 'month', order='DESC')[:12]

    context = {
        'empresas': empresas,
        'empresa': empresa,
        'mes': mes,
        'ano': ano,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'lucro_bruto': lucro_bruto,
        'cat_entradas': cat_entradas,
        'cat_saidas': cat_saidas,
        'retirada_renan': retirada_renan,
        'retirada_renan_liquida': retirada_renan_liquida,
        'prestacoes_renan': prestacoes_renan,
        'retirada_yuri': retirada_yuri,
        'retiradas_yuri_detalhe': retiradas_yuri_detalhe,
        'custos_operacionais': custos_operacionais,
        'custos_operacionais_total': custos_operacionais_total,
        'lucro_liquido': lucro_liquido,
        'direito_cada': direito_cada,
        'saldo_yuri': saldo_yuri,
        'saldo_renan': saldo_renan,
        'prestacoes_detalhe': prestacoes_detalhe,
        'meses_disponiveis': meses_disponiveis,
    }
    return render(request, 'financeiro/relatorio.html', context)


@login_required
@require_POST
def registrar_retirada(request):
    """Registra pagamento recebido do Renan (retirada Yuri) sem afetar saldo do MP."""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresa = get_object_or_404(Empresa, id=request.POST.get('empresa'))
    descricao = request.POST.get('descricao', '').strip()
    valor = request.POST.get('valor', '0').replace(',', '.')
    data = request.POST.get('data')
    mes = request.POST.get('mes', timezone.localdate().month)
    ano = request.POST.get('ano', timezone.localdate().year)

    try:
        valor = Decimal(valor)
    except Exception:
        messages.error(request, 'Valor inválido.')
        return redirect(f'/financeiro/relatorio/?empresa={empresa.id}&mes={mes}&ano={ano}')

    if not descricao or not data:
        messages.error(request, 'Preencha todos os campos.')
        return redirect(f'/financeiro/relatorio/?empresa={empresa.id}&mes={mes}&ano={ano}')

    # Busca categoria "Retirada Yuri"
    cat_yuri = CategoriaLancamento.objects.filter(
        empresa=empresa, nome='Retirada Yuri', tipo='saida'
    ).first()

    # Cria lançamento SEM conta bancária (não afeta saldo do MP)
    Lancamento.objects.create(
        empresa=empresa,
        conta=None,
        tipo='saida',
        categoria=cat_yuri,
        descricao=descricao,
        valor=valor,
        data=data,
        observacao='Pagamento recebido do Renan (por fora)',
        criado_por=pessoa,
    )
    messages.success(request, f'Retirada de R$ {valor:,.2f} registrada.')
    return redirect(f'/financeiro/relatorio/?empresa={empresa.id}&mes={mes}&ano={ano}')


@login_required
def contas_pagar(request):
    """CRUD de contas a pagar recorrentes + visão do mês"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = Empresa.objects.all()
    hoje = timezone.localdate()
    empresa_id = request.GET.get('empresa')

    if empresa_id:
        empresa = get_object_or_404(Empresa, id=empresa_id)
    elif empresas.exists():
        empresa = empresas.first()
    else:
        return render(request, 'financeiro/contas_pagar.html', {'empresas': empresas})

    if request.method == 'POST':
        action = request.POST.get('action', 'criar')

        if action == 'excluir':
            conta_id = request.POST.get('conta_id')
            conta = get_object_or_404(ContaPagar, id=conta_id, empresa=empresa)
            conta.ativo = False
            conta.save()
            # Excluir itens pendentes (não pagos)
            conta.itens.filter(pago=False).delete()
            messages.success(request, f'Conta "{conta.descricao}" desativada.')
            return redirect(f'/financeiro/contas-pagar/?empresa={empresa.id}')

        empresa_post_id = request.POST.get('empresa')
        if not empresa_post_id:
            messages.error(request, 'Selecione uma empresa.')
            return redirect('contas_pagar')
        empresa = get_object_or_404(Empresa, id=empresa_post_id)
        descricao = request.POST.get('descricao', '').strip()
        valor = request.POST.get('valor', '0').replace(',', '.')
        categoria_id = request.POST.get('categoria') or None
        conta_bancaria_id = request.POST.get('conta_bancaria') or None

        # Data do vencimento (obrigatória)
        data_vencimento_str = request.POST.get('data_vencimento', '').strip()
        if not data_vencimento_str:
            messages.error(request, 'Data do vencimento é obrigatória.')
            return redirect(f'/financeiro/contas-pagar/?empresa={empresa.id}')
        from datetime import datetime
        data_vencimento = datetime.strptime(data_vencimento_str, '%Y-%m-%d').date()
        dia_vencimento = data_vencimento.day  # Extrai automaticamente

        dia_execucao = request.POST.get('dia_execucao', 'mesmo_dia')
        dia_execucao_mensal = request.POST.get('dia_execucao_mensal') or None
        if dia_execucao_mensal:
            dia_execucao_mensal = int(dia_execucao_mensal)
        recorrencia = request.POST.get('recorrencia', 'mensal')
        observacao = request.POST.get('observacao', '').strip()

        try:
            valor = Decimal(valor)
        except Exception:
            messages.error(request, 'Valor inválido.')
            return redirect(f'/financeiro/contas-pagar/?empresa={empresa.id}')

        if not descricao:
            messages.error(request, 'Descrição obrigatória.')
            return redirect(f'/financeiro/contas-pagar/?empresa={empresa.id}')

        # Parcelamento
        parcelado = request.POST.get('parcelado') == 'on'
        total_parcelas = int(request.POST.get('total_parcelas', 1) or 1)
        if total_parcelas < 1:
            total_parcelas = 1

        valor_total = None
        if parcelado and total_parcelas > 1:
            valor_total = valor  # valor informado é o total
            valor = valor / total_parcelas  # valor da parcela
            recorrencia = 'parcelada'

        conta = ContaPagar.objects.create(
            empresa=empresa,
            descricao=descricao,
            valor=valor,
            valor_total=valor_total,
            categoria_id=categoria_id,
            conta_id=conta_bancaria_id,
            data_vencimento=data_vencimento,
            dia_vencimento=dia_vencimento,
            dia_execucao=dia_execucao,
            dia_execucao_mensal=dia_execucao_mensal,
            recorrencia=recorrencia,
            observacao=observacao,
            parcelado=parcelado,
            total_parcelas=total_parcelas,
        )

        # Se parcelado, gerar todas as parcelas de uma vez
        if parcelado and total_parcelas > 1:
            from .services import gerar_parcelas_conta
            gerar_parcelas_conta(conta)
            messages.success(request, f'Conta "{descricao}" criada com {total_parcelas} parcelas de R$ {valor:,.2f}.')
        else:
            # Gerar item do mês da data de vencimento
            from .services import gerar_contas_pagar_mes
            gerar_contas_pagar_mes(empresa, data_vencimento.month, data_vencimento.year)
            messages.success(request, f'Conta "{descricao}" criada.')
        return redirect(f'/financeiro/contas-pagar/?empresa={empresa.id}')

    # Listar contas recorrentes ativas
    contas = ContaPagar.objects.filter(empresa=empresa, ativo=True).select_related('categoria', 'conta')

    # Itens do mês atual
    itens_mes = ContaPagarItem.objects.filter(
        conta_pagar__empresa=empresa,
        mes=hoje.month,
        ano=hoje.year,
    ).select_related('conta_pagar', 'lancamento').order_by('data_vencimento')

    total_mes = sum(i.valor for i in itens_mes)
    total_pago = sum(i.valor for i in itens_mes if i.pago)
    total_pendente = total_mes - total_pago

    categorias = CategoriaLancamento.objects.filter(
        Q(empresa=empresa) | Q(empresa__isnull=True), ativo=True, tipo='saida'
    ).order_by('ordem', 'nome')

    contas_bancarias = ContaBancaria.objects.filter(empresa=empresa, ativo=True)

    context = {
        'empresas': empresas,
        'empresa': empresa,
        'contas': contas,
        'itens_mes': itens_mes,
        'hoje': hoje,
        'total_mes': total_mes,
        'total_pago': total_pago,
        'total_pendente': total_pendente,
        'categorias': categorias,
        'contas_bancarias': contas_bancarias,
        'dias_execucao': ContaPagar.DIA_EXECUCAO_CHOICES,
        'recorrencias': ContaPagar.RECORRENCIA_CHOICES,
    }
    return render(request, 'financeiro/contas_pagar.html', context)


@login_required
@require_POST
def pagar_conta(request, item_id):
    """Marca um item de conta a pagar como pago e cria lançamento"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    item = get_object_or_404(ContaPagarItem, id=item_id)

    if item.pago:
        messages.warning(request, 'Esta conta já foi paga.')
        return redirect(request.META.get('HTTP_REFERER', 'contas_pagar'))

    # Criar lançamento de saída
    lancamento = Lancamento.objects.create(
        empresa=item.conta_pagar.empresa,
        conta=item.conta_pagar.conta,
        tipo='saida',
        categoria=item.conta_pagar.categoria,
        descricao=f'{item.conta_pagar.descricao} - {item.mes:02d}/{item.ano}',
        valor=item.valor,
        data=timezone.localdate(),
        observacao=f'Conta a pagar recorrente (venc. {item.data_vencimento.strftime("%d/%m/%Y")})',
        criado_por=pessoa,
    )

    item.pago = True
    item.pago_em = timezone.now()
    item.lancamento = lancamento
    item.save()

    messages.success(request, f'Conta "{item.conta_pagar.descricao}" paga - Lançamento de R$ {item.valor:,.2f} criado.')
    return redirect(request.META.get('HTTP_REFERER', 'contas_pagar'))


# =====================================================
# CONTAS A RECEBER
# =====================================================

@login_required
def contas_receber(request):
    """CRUD de contas a receber + visão do mês"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = Empresa.objects.all()
    hoje = timezone.localdate()
    empresa_id = request.GET.get('empresa')

    if empresa_id:
        empresa = get_object_or_404(Empresa, id=empresa_id)
    elif empresas.exists():
        empresa = empresas.first()
    else:
        return render(request, 'financeiro/contas_receber.html', {'empresas': empresas})

    if request.method == 'POST':
        action = request.POST.get('action', 'criar')

        if action == 'excluir':
            conta_id = request.POST.get('conta_id')
            conta = get_object_or_404(ContaReceber, id=conta_id, empresa=empresa)
            conta.ativo = False
            conta.save()
            # Excluir itens pendentes (não recebidos)
            conta.itens.filter(recebido=False).delete()
            messages.success(request, f'Conta a receber "{conta.descricao}" desativada.')
            return redirect(f'/financeiro/contas-receber/?empresa={empresa.id}')

        empresa_post_id = request.POST.get('empresa')
        if not empresa_post_id:
            messages.error(request, 'Selecione uma empresa.')
            return redirect('contas_receber')
        empresa = get_object_or_404(Empresa, id=empresa_post_id)
        descricao = request.POST.get('descricao', '').strip()
        valor = request.POST.get('valor', '0').replace(',', '.')
        categoria_id = request.POST.get('categoria') or None
        conta_bancaria_id = request.POST.get('conta_bancaria') or None
        cliente_id = request.POST.get('cliente') or None
        projeto_id = request.POST.get('projeto') or None

        # Data do vencimento (obrigatória)
        data_vencimento_str = request.POST.get('data_vencimento', '').strip()
        if not data_vencimento_str:
            messages.error(request, 'Data do vencimento é obrigatória.')
            return redirect(f'/financeiro/contas-receber/?empresa={empresa.id}')
        from datetime import datetime
        data_vencimento = datetime.strptime(data_vencimento_str, '%Y-%m-%d').date()
        dia_vencimento = data_vencimento.day

        recorrencia = request.POST.get('recorrencia', 'mensal')
        observacao = request.POST.get('observacao', '').strip()
        notificar_cliente = request.POST.get('notificar_cliente') == 'on'
        dias_antecedencia = int(request.POST.get('dias_antecedencia', 3) or 3)

        try:
            valor = Decimal(valor)
        except Exception:
            messages.error(request, 'Valor inválido.')
            return redirect(f'/financeiro/contas-receber/?empresa={empresa.id}')

        if not descricao:
            messages.error(request, 'Descrição obrigatória.')
            return redirect(f'/financeiro/contas-receber/?empresa={empresa.id}')

        # Parcelamento
        parcelado = request.POST.get('parcelado') == 'on'
        total_parcelas = int(request.POST.get('total_parcelas', 1) or 1)
        if total_parcelas < 1:
            total_parcelas = 1

        valor_total = None
        if parcelado and total_parcelas > 1:
            valor_total = valor  # valor informado é o total
            valor = valor / total_parcelas  # valor da parcela
            recorrencia = 'parcelada'

        conta = ContaReceber.objects.create(
            empresa=empresa,
            cliente_id=cliente_id,
            projeto_id=projeto_id,
            descricao=descricao,
            valor=valor,
            valor_total=valor_total,
            categoria_id=categoria_id,
            conta_id=conta_bancaria_id,
            data_vencimento=data_vencimento,
            dia_vencimento=dia_vencimento,
            recorrencia=recorrencia,
            observacao=observacao,
            notificar_cliente=notificar_cliente,
            dias_antecedencia=dias_antecedencia,
            parcelado=parcelado,
            total_parcelas=total_parcelas,
        )

        # Se parcelado, gerar todas as parcelas de uma vez
        if parcelado and total_parcelas > 1:
            from .services import gerar_parcelas_conta_receber
            gerar_parcelas_conta_receber(conta)
            messages.success(request, f'Conta a receber "{descricao}" criada com {total_parcelas} parcelas de R$ {valor:,.2f}.')
        else:
            # Gerar item do mês da data de vencimento
            from .services import gerar_contas_receber_mes
            gerar_contas_receber_mes(empresa, data_vencimento.month, data_vencimento.year)
            messages.success(request, f'Conta a receber "{descricao}" criada.')
        return redirect(f'/financeiro/contas-receber/?empresa={empresa.id}')

    # Listar contas recorrentes ativas
    contas = ContaReceber.objects.filter(empresa=empresa, ativo=True).select_related('categoria', 'conta', 'cliente', 'projeto')

    # Itens do mês atual
    itens_mes = ContaReceberItem.objects.filter(
        conta_receber__empresa=empresa,
        mes=hoje.month,
        ano=hoje.year,
    ).select_related('conta_receber', 'conta_receber__cliente', 'lancamento').order_by('data_vencimento')

    total_mes = sum(i.valor for i in itens_mes)
    total_recebido = sum(i.valor_recebido or i.valor for i in itens_mes if i.recebido)
    total_pendente = total_mes - total_recebido
    total_atrasado = sum(i.valor for i in itens_mes if i.esta_atrasado)

    categorias = CategoriaLancamento.objects.filter(
        Q(empresa=empresa) | Q(empresa__isnull=True), ativo=True, tipo='entrada'
    ).order_by('ordem', 'nome')

    contas_bancarias = ContaBancaria.objects.filter(empresa=empresa, ativo=True)
    clientes = Pessoa.objects.filter(empresas=empresa)
    projetos = Projeto.objects.filter(empresa=empresa, status__in=['em_andamento', 'planejamento'])

    context = {
        'empresas': empresas,
        'empresa': empresa,
        'contas': contas,
        'itens_mes': itens_mes,
        'hoje': hoje,
        'total_mes': total_mes,
        'total_recebido': total_recebido,
        'total_pendente': total_pendente,
        'total_atrasado': total_atrasado,
        'categorias': categorias,
        'contas_bancarias': contas_bancarias,
        'clientes': clientes,
        'projetos': projetos,
        'recorrencias': ContaReceber.RECORRENCIA_CHOICES,
    }
    return render(request, 'financeiro/contas_receber.html', context)


@login_required
@require_POST
def receber_conta(request, item_id):
    """Marca um item de conta a receber como recebido e cria lançamento"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    item = get_object_or_404(ContaReceberItem, id=item_id)

    if item.recebido:
        messages.warning(request, 'Esta conta já foi recebida.')
        return redirect(request.META.get('HTTP_REFERER', 'contas_receber'))

    # Valor efetivamente recebido (pode ser diferente do esperado)
    valor_recebido = request.POST.get('valor_recebido', '').replace(',', '.')
    if valor_recebido:
        try:
            valor_recebido = Decimal(valor_recebido)
        except Exception:
            valor_recebido = item.valor
    else:
        valor_recebido = item.valor

    # Criar lançamento de entrada
    lancamento = Lancamento.objects.create(
        empresa=item.conta_receber.empresa,
        conta=item.conta_receber.conta,
        tipo='entrada',
        categoria=item.conta_receber.categoria,
        projeto=item.conta_receber.projeto,
        pessoa=item.conta_receber.cliente,
        descricao=f'{item.conta_receber.descricao} - {item.mes:02d}/{item.ano}',
        valor=valor_recebido,
        data=timezone.localdate(),
        observacao=f'Conta a receber (venc. {item.data_vencimento.strftime("%d/%m/%Y")})',
        criado_por=pessoa,
    )

    item.recebido = True
    item.recebido_em = timezone.now()
    item.valor_recebido = valor_recebido
    item.status = 'recebido'
    item.lancamento = lancamento
    item.save()

    messages.success(request, f'Recebimento de "{item.conta_receber.descricao}" - R$ {valor_recebido:,.2f} registrado.')
    return redirect(request.META.get('HTTP_REFERER', 'contas_receber'))


@login_required
@require_POST
def cancelar_conta_receber(request, item_id):
    """Cancela um item de conta a receber"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    item = get_object_or_404(ContaReceberItem, id=item_id)

    if item.recebido:
        messages.warning(request, 'Esta conta já foi recebida e não pode ser cancelada.')
        return redirect(request.META.get('HTTP_REFERER', 'contas_receber'))

    motivo = request.POST.get('motivo', '').strip()
    item.status = 'cancelado'
    item.observacao = f'Cancelado: {motivo}' if motivo else 'Cancelado pelo usuário'
    item.save()

    messages.success(request, f'Conta a receber "{item.conta_receber.descricao}" cancelada.')
    return redirect(request.META.get('HTTP_REFERER', 'contas_receber'))


@login_required
def detalhe_conta_receber(request, conta_id):
    """Exibe todos os itens/parcelas de uma conta a receber"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    conta = get_object_or_404(ContaReceber, id=conta_id)
    itens = conta.itens.all().order_by('data_vencimento')

    context = {
        'conta': conta,
        'itens': itens,
        'total_recebido': conta.get_total_recebido(),
        'total_pendente': conta.get_total_pendente(),
        'total_atrasado': conta.get_total_atrasado(),
    }
    return render(request, 'financeiro/detalhe_conta_receber.html', context)


# =====================================================
# FLUXO DE CAIXA PROJETADO
# =====================================================

@login_required
def fluxo_caixa(request):
    """Fluxo de caixa projetado - visao de entradas e saidas futuras"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = Empresa.objects.all()
    hoje = timezone.localdate()
    empresa_id = request.GET.get('empresa')
    meses_frente = int(request.GET.get('meses', 3))  # Padrao: 3 meses

    if empresa_id:
        empresa = get_object_or_404(Empresa, id=empresa_id)
    elif empresas.exists():
        empresa = empresas.first()
    else:
        return render(request, 'financeiro/fluxo_caixa.html', {'empresas': empresas})

    # Saldo atual das contas bancarias
    contas_bancarias = ContaBancaria.objects.filter(empresa=empresa, ativo=True)
    saldo_atual = sum(c.get_saldo() for c in contas_bancarias)

    # Gerar projecao para os proximos meses
    from dateutil.relativedelta import relativedelta
    import calendar

    projecao = []
    saldo_acumulado = saldo_atual

    for i in range(meses_frente):
        data_mes = hoje + relativedelta(months=i)
        mes = data_mes.month
        ano = data_mes.year

        # Contas a pagar do mes
        itens_pagar = ContaPagarItem.objects.filter(
            conta_pagar__empresa=empresa,
            mes=mes,
            ano=ano,
            pago=False,
        ).select_related('conta_pagar')
        total_pagar = sum(i.valor for i in itens_pagar)

        # Contas a receber do mes
        itens_receber = ContaReceberItem.objects.filter(
            conta_receber__empresa=empresa,
            mes=mes,
            ano=ano,
            recebido=False,
            status__in=['pendente', 'atrasado'],
        ).select_related('conta_receber')
        total_receber = sum(i.valor for i in itens_receber)

        # Saldo projetado
        saldo_mes = total_receber - total_pagar
        saldo_acumulado += saldo_mes

        projecao.append({
            'mes': mes,
            'ano': ano,
            'nome_mes': calendar.month_name[mes],
            'a_pagar': total_pagar,
            'a_receber': total_receber,
            'saldo_mes': saldo_mes,
            'saldo_acumulado': saldo_acumulado,
            'itens_pagar': itens_pagar,
            'itens_receber': itens_receber,
        })

    # Totais gerais
    total_a_pagar = sum(p['a_pagar'] for p in projecao)
    total_a_receber = sum(p['a_receber'] for p in projecao)

    context = {
        'empresas': empresas,
        'empresa': empresa,
        'hoje': hoje,
        'meses_frente': meses_frente,
        'projecao': projecao,
        'saldo_atual': saldo_atual,
        'total_a_pagar': total_a_pagar,
        'total_a_receber': total_a_receber,
        'saldo_final_projetado': saldo_acumulado,
        'contas_bancarias': contas_bancarias,
    }
    return render(request, 'financeiro/fluxo_caixa.html', context)


# =====================================================
# DRE SIMPLIFICADO
# =====================================================

@login_required
def dre_simplificado(request):
    """DRE Simplificado - Demonstrativo de Resultado do Exercicio"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = Empresa.objects.all()
    hoje = timezone.localdate()
    empresa_id = request.GET.get('empresa')
    mes = int(request.GET.get('mes', hoje.month))
    ano = int(request.GET.get('ano', hoje.year))

    if empresa_id:
        empresa = get_object_or_404(Empresa, id=empresa_id)
    elif empresas.exists():
        empresa = empresas.first()
    else:
        return render(request, 'financeiro/dre.html', {'empresas': empresas})

    # Lancamentos do mes
    lancamentos = Lancamento.objects.filter(
        empresa=empresa, data__month=mes, data__year=ano
    ).select_related('categoria')

    # RECEITA BRUTA (todas as entradas)
    receita_bruta = lancamentos.filter(tipo='entrada').aggregate(
        total=Sum('valor'))['total'] or Decimal('0')

    # Deducoes (taxas, impostos - categorias especificas)
    categorias_deducao = ['Taxa MP', 'Impostos', 'Taxa', 'Taxas']
    deducoes = lancamentos.filter(
        tipo='saida',
        categoria__nome__in=categorias_deducao
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0')

    # RECEITA LIQUIDA
    receita_liquida = receita_bruta - deducoes

    # CUSTOS OPERACIONAIS (saidas que nao sao retirada e nao sao deducao)
    categorias_retirada = ['Retirada Renan', 'Retirada Yuri', 'Retirada', 'Pro-Labore']
    custos_operacionais = lancamentos.filter(tipo='saida').exclude(
        categoria__nome__in=categorias_retirada + categorias_deducao
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0')

    # LUCRO OPERACIONAL
    lucro_operacional = receita_liquida - custos_operacionais

    # DESPESAS NAO OPERACIONAIS (retiradas)
    despesas_nao_operacionais = lancamentos.filter(
        tipo='saida',
        categoria__nome__in=categorias_retirada
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0')

    # LUCRO LIQUIDO
    lucro_liquido = lucro_operacional - despesas_nao_operacionais

    # Margem de lucro
    margem_bruta = (receita_liquida / receita_bruta * 100) if receita_bruta > 0 else 0
    margem_liquida = (lucro_liquido / receita_bruta * 100) if receita_bruta > 0 else 0

    # Detalhamento por categoria
    entradas_por_categoria = lancamentos.filter(tipo='entrada').values(
        'categoria__nome', 'categoria__cor'
    ).annotate(total=Sum('valor')).order_by('-total')

    saidas_por_categoria = lancamentos.filter(tipo='saida').values(
        'categoria__nome', 'categoria__cor'
    ).annotate(total=Sum('valor')).order_by('-total')

    # Comparativo com mes anterior
    from dateutil.relativedelta import relativedelta
    data_anterior = hoje.replace(day=1) - relativedelta(months=1)
    mes_anterior = data_anterior.month
    ano_anterior = data_anterior.year

    lancamentos_ant = Lancamento.objects.filter(
        empresa=empresa, data__month=mes_anterior, data__year=ano_anterior
    )
    receita_ant = lancamentos_ant.filter(tipo='entrada').aggregate(
        total=Sum('valor'))['total'] or Decimal('0')
    lucro_ant = receita_ant - (lancamentos_ant.filter(tipo='saida').aggregate(
        total=Sum('valor'))['total'] or Decimal('0'))

    variacao_receita = ((receita_bruta - receita_ant) / receita_ant * 100) if receita_ant > 0 else 0
    variacao_lucro = ((lucro_liquido - lucro_ant) / abs(lucro_ant) * 100) if lucro_ant != 0 else 0

    # Meses disponiveis
    meses_disponiveis = Lancamento.objects.filter(empresa=empresa).dates('data', 'month', order='DESC')[:24]

    context = {
        'empresas': empresas,
        'empresa': empresa,
        'mes': mes,
        'ano': ano,
        'hoje': hoje,
        # DRE
        'receita_bruta': receita_bruta,
        'deducoes': deducoes,
        'receita_liquida': receita_liquida,
        'custos_operacionais': custos_operacionais,
        'lucro_operacional': lucro_operacional,
        'despesas_nao_operacionais': despesas_nao_operacionais,
        'lucro_liquido': lucro_liquido,
        # Margens
        'margem_bruta': margem_bruta,
        'margem_liquida': margem_liquida,
        # Detalhamento
        'entradas_por_categoria': entradas_por_categoria,
        'saidas_por_categoria': saidas_por_categoria,
        # Comparativo
        'mes_anterior': mes_anterior,
        'ano_anterior': ano_anterior,
        'receita_anterior': receita_ant,
        'lucro_anterior': lucro_ant,
        'variacao_receita': variacao_receita,
        'variacao_lucro': variacao_lucro,
        # Navegacao
        'meses_disponiveis': meses_disponiveis,
    }
    return render(request, 'financeiro/dre.html', context)


# =====================================================
# ALERTAS FINANCEIROS
# =====================================================

@login_required
def alertas_financeiros(request):
    """Gerenciamento de alertas financeiros"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = Empresa.objects.all()
    empresa_id = request.GET.get('empresa')

    if empresa_id:
        empresa = get_object_or_404(Empresa, id=empresa_id)
    elif empresas.exists():
        empresa = empresas.first()
    else:
        return render(request, 'financeiro/alertas.html', {'empresas': empresas})

    if request.method == 'POST':
        action = request.POST.get('action', 'criar')

        if action == 'excluir':
            alerta_id = request.POST.get('alerta_id')
            alerta = get_object_or_404(AlertaFinanceiro, id=alerta_id, empresa=empresa)
            alerta.delete()
            messages.success(request, 'Alerta excluido.')
            return redirect(f'/financeiro/alertas/?empresa={empresa.id}')

        if action == 'toggle':
            alerta_id = request.POST.get('alerta_id')
            alerta = get_object_or_404(AlertaFinanceiro, id=alerta_id, empresa=empresa)
            alerta.ativo = not alerta.ativo
            alerta.save()
            status = 'ativado' if alerta.ativo else 'desativado'
            messages.success(request, f'Alerta {status}.')
            return redirect(f'/financeiro/alertas/?empresa={empresa.id}')

        # Criar novo alerta
        empresa_post_id = request.POST.get('empresa')
        if not empresa_post_id:
            messages.error(request, 'Selecione uma empresa.')
            return redirect('alertas_financeiros')
        empresa = get_object_or_404(Empresa, id=empresa_post_id)
        tipo = request.POST.get('tipo')
        dias_antecedencia = int(request.POST.get('dias_antecedencia', 3))
        valor_limite = request.POST.get('valor_limite', '').replace(',', '.')
        notificar_whatsapp = request.POST.get('notificar_whatsapp') == 'on'
        destinatarios_ids = request.POST.getlist('destinatarios')

        if not tipo:
            messages.error(request, 'Selecione o tipo de alerta.')
            return redirect(f'/financeiro/alertas/?empresa={empresa.id}')

        alerta = AlertaFinanceiro.objects.create(
            empresa=empresa,
            tipo=tipo,
            dias_antecedencia=dias_antecedencia,
            valor_limite=Decimal(valor_limite) if valor_limite else None,
            notificar_whatsapp=notificar_whatsapp,
        )
        if destinatarios_ids:
            alerta.destinatarios.set(destinatarios_ids)

        messages.success(request, f'Alerta "{alerta.get_tipo_display()}" criado.')
        return redirect(f'/financeiro/alertas/?empresa={empresa.id}')

    # Listar alertas
    alertas = AlertaFinanceiro.objects.filter(empresa=empresa).prefetch_related('destinatarios')

    # Historico recente
    historico = HistoricoAlerta.objects.filter(alerta__empresa=empresa).select_related('alerta')[:20]

    # Pessoas para destinatarios
    pessoas = Pessoa.objects.filter(empresas=empresa)

    # Preview de alertas pendentes
    hoje = timezone.localdate()
    preview_alertas = []

    # Contas a pagar vencendo
    contas_pagar_vencendo = ContaPagarItem.objects.filter(
        conta_pagar__empresa=empresa,
        pago=False,
        data_vencimento__gte=hoje,
        data_vencimento__lte=hoje + timedelta(days=3),
    ).select_related('conta_pagar')[:5]
    if contas_pagar_vencendo:
        preview_alertas.append({
            'tipo': 'Contas a Pagar Vencendo',
            'itens': [f"{c.conta_pagar.descricao} - R$ {c.valor} (vence {c.data_vencimento.strftime('%d/%m')})" for c in contas_pagar_vencendo],
            'cor': 'yellow',
        })

    # Contas a pagar atrasadas
    contas_pagar_atrasadas = ContaPagarItem.objects.filter(
        conta_pagar__empresa=empresa,
        pago=False,
        data_vencimento__lt=hoje,
    ).select_related('conta_pagar')[:5]
    if contas_pagar_atrasadas:
        preview_alertas.append({
            'tipo': 'Contas a Pagar Atrasadas',
            'itens': [f"{c.conta_pagar.descricao} - R$ {c.valor} ({(hoje - c.data_vencimento).days} dias)" for c in contas_pagar_atrasadas],
            'cor': 'red',
        })

    # Contas a receber vencendo
    contas_receber_vencendo = ContaReceberItem.objects.filter(
        conta_receber__empresa=empresa,
        recebido=False,
        status__in=['pendente'],
        data_vencimento__gte=hoje,
        data_vencimento__lte=hoje + timedelta(days=3),
    ).select_related('conta_receber')[:5]
    if contas_receber_vencendo:
        preview_alertas.append({
            'tipo': 'Contas a Receber Vencendo',
            'itens': [f"{c.conta_receber.descricao} - R$ {c.valor} (vence {c.data_vencimento.strftime('%d/%m')})" for c in contas_receber_vencendo],
            'cor': 'blue',
        })

    # Contas a receber atrasadas
    contas_receber_atrasadas = ContaReceberItem.objects.filter(
        conta_receber__empresa=empresa,
        recebido=False,
        data_vencimento__lt=hoje,
    ).exclude(status='cancelado').select_related('conta_receber')[:5]
    if contas_receber_atrasadas:
        preview_alertas.append({
            'tipo': 'Contas a Receber Atrasadas',
            'itens': [f"{c.conta_receber.descricao} - R$ {c.valor} ({(hoje - c.data_vencimento).days} dias)" for c in contas_receber_atrasadas],
            'cor': 'orange',
        })

    context = {
        'empresas': empresas,
        'empresa': empresa,
        'alertas': alertas,
        'historico': historico,
        'pessoas': pessoas,
        'tipos_alerta': AlertaFinanceiro.TIPO_ALERTA_CHOICES,
        'preview_alertas': preview_alertas,
    }
    return render(request, 'financeiro/alertas.html', context)


@login_required
@require_POST
def enviar_alerta_teste(request):
    """Envia um alerta de teste via WhatsApp"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return JsonResponse({'error': 'Nao autorizado'}, status=403)

    alerta_id = request.POST.get('alerta_id')
    alerta = get_object_or_404(AlertaFinanceiro, id=alerta_id)

    # Simular envio (integracao real com WAPI seria implementada aqui)
    mensagem = f"[TESTE] Alerta {alerta.get_tipo_display()} - {alerta.empresa.nome}"

    HistoricoAlerta.objects.create(
        alerta=alerta,
        mensagem=mensagem,
        sucesso=True,
    )

    messages.success(request, f'Alerta de teste enviado: {alerta.get_tipo_display()}')
    return redirect(request.META.get('HTTP_REFERER', 'alertas_financeiros'))


# =====================================================
# RELATORIO POR PROJETO
# =====================================================

@login_required
def relatorio_projeto(request):
    """Relatorio financeiro por projeto - rentabilidade"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = Empresa.objects.all()
    empresa_id = request.GET.get('empresa')
    projeto_id = request.GET.get('projeto')

    if empresa_id:
        empresa = get_object_or_404(Empresa, id=empresa_id)
    elif empresas.exists():
        empresa = empresas.first()
    else:
        return render(request, 'financeiro/relatorio_projeto.html', {'empresas': empresas})

    # Projetos da empresa
    projetos = Projeto.objects.filter(empresa=empresa).order_by('-criado_em')

    projeto = None
    dados_projeto = None

    if projeto_id:
        projeto = get_object_or_404(Projeto, id=projeto_id, empresa=empresa)

        # Lancamentos do projeto
        lancamentos = Lancamento.objects.filter(empresa=empresa, projeto=projeto)

        # Receitas do projeto
        receitas = lancamentos.filter(tipo='entrada')
        total_receitas = receitas.aggregate(total=Sum('valor'))['total'] or Decimal('0')

        # Despesas do projeto
        despesas = lancamentos.filter(tipo='saida')
        total_despesas = despesas.aggregate(total=Sum('valor'))['total'] or Decimal('0')

        # Lucro
        lucro = total_receitas - total_despesas
        margem = (lucro / total_receitas * 100) if total_receitas > 0 else 0

        # Contas a receber do projeto
        a_receber = ContaReceber.objects.filter(empresa=empresa, projeto=projeto, ativo=True)
        total_a_receber = sum(c.get_total_pendente() for c in a_receber)

        # Por categoria
        receitas_categoria = receitas.values('categoria__nome', 'categoria__cor').annotate(
            total=Sum('valor')).order_by('-total')
        despesas_categoria = despesas.values('categoria__nome', 'categoria__cor').annotate(
            total=Sum('valor')).order_by('-total')

        # Timeline (por mes)
        from django.db.models.functions import TruncMonth
        timeline = lancamentos.annotate(mes=TruncMonth('data')).values('mes', 'tipo').annotate(
            total=Sum('valor')).order_by('mes')

        dados_projeto = {
            'total_receitas': total_receitas,
            'total_despesas': total_despesas,
            'lucro': lucro,
            'margem': margem,
            'total_a_receber': total_a_receber,
            'receitas_categoria': receitas_categoria,
            'despesas_categoria': despesas_categoria,
            'lancamentos': lancamentos[:20],
            'timeline': timeline,
        }

    # Resumo de todos os projetos
    resumo_projetos = []
    for p in projetos[:10]:
        lanc = Lancamento.objects.filter(empresa=empresa, projeto=p)
        receita = lanc.filter(tipo='entrada').aggregate(t=Sum('valor'))['t'] or Decimal('0')
        despesa = lanc.filter(tipo='saida').aggregate(t=Sum('valor'))['t'] or Decimal('0')
        lucro_p = receita - despesa
        margem_p = (lucro_p / receita * 100) if receita > 0 else 0
        resumo_projetos.append({
            'projeto': p,
            'receita': receita,
            'despesa': despesa,
            'lucro': lucro_p,
            'margem': margem_p,
        })

    # Ordenar por lucro
    resumo_projetos.sort(key=lambda x: x['lucro'], reverse=True)

    context = {
        'empresas': empresas,
        'empresa': empresa,
        'projetos': projetos,
        'projeto': projeto,
        'dados': dados_projeto,
        'resumo_projetos': resumo_projetos,
    }
    return render(request, 'financeiro/relatorio_projeto.html', context)


# =====================================================
# COMPARATIVO MES A MES
# =====================================================

@login_required
def comparativo_mensal(request):
    """Comparativo financeiro mes a mes"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = Empresa.objects.all()
    empresa_id = request.GET.get('empresa')
    meses_comparar = int(request.GET.get('meses', 6))  # Padrao: 6 meses

    if empresa_id:
        empresa = get_object_or_404(Empresa, id=empresa_id)
    elif empresas.exists():
        empresa = empresas.first()
    else:
        return render(request, 'financeiro/comparativo.html', {'empresas': empresas})

    from dateutil.relativedelta import relativedelta
    import calendar

    hoje = timezone.localdate()
    dados_meses = []

    for i in range(meses_comparar - 1, -1, -1):
        data_mes = hoje - relativedelta(months=i)
        mes = data_mes.month
        ano = data_mes.year

        lancamentos = Lancamento.objects.filter(
            empresa=empresa, data__month=mes, data__year=ano
        )

        receitas = lancamentos.filter(tipo='entrada').aggregate(t=Sum('valor'))['t'] or Decimal('0')
        despesas = lancamentos.filter(tipo='saida').aggregate(t=Sum('valor'))['t'] or Decimal('0')
        lucro = receitas - despesas

        # Meta do mes
        meta = MetaEmpresa.objects.filter(empresa=empresa, mes=mes, ano=ano).first()
        valor_meta = meta.valor_meta if meta else Decimal('0')
        progresso_meta = (receitas / valor_meta * 100) if valor_meta > 0 else 0

        # Categorias principais
        top_receitas = lancamentos.filter(tipo='entrada').values(
            'categoria__nome').annotate(total=Sum('valor')).order_by('-total')[:3]
        top_despesas = lancamentos.filter(tipo='saida').values(
            'categoria__nome').annotate(total=Sum('valor')).order_by('-total')[:3]

        dados_meses.append({
            'mes': mes,
            'ano': ano,
            'nome_mes': calendar.month_abbr[mes],
            'receitas': receitas,
            'despesas': despesas,
            'lucro': lucro,
            'margem': (lucro / receitas * 100) if receitas > 0 else 0,
            'meta': valor_meta,
            'progresso_meta': progresso_meta,
            'top_receitas': top_receitas,
            'top_despesas': top_despesas,
        })

    # Calcular variacoes
    for i in range(1, len(dados_meses)):
        atual = dados_meses[i]
        anterior = dados_meses[i - 1]

        atual['var_receita'] = ((atual['receitas'] - anterior['receitas']) / anterior['receitas'] * 100) if anterior['receitas'] > 0 else 0
        atual['var_despesa'] = ((atual['despesas'] - anterior['despesas']) / anterior['despesas'] * 100) if anterior['despesas'] > 0 else 0
        atual['var_lucro'] = ((atual['lucro'] - anterior['lucro']) / abs(anterior['lucro']) * 100) if anterior['lucro'] != 0 else 0

    # Totais e medias
    total_receitas = sum(m['receitas'] for m in dados_meses)
    total_despesas = sum(m['despesas'] for m in dados_meses)
    total_lucro = total_receitas - total_despesas
    media_receitas = total_receitas / len(dados_meses) if dados_meses else 0
    media_lucro = total_lucro / len(dados_meses) if dados_meses else 0

    # Melhor e pior mes
    melhor_mes = max(dados_meses, key=lambda x: x['lucro']) if dados_meses else None
    pior_mes = min(dados_meses, key=lambda x: x['lucro']) if dados_meses else None

    context = {
        'empresas': empresas,
        'empresa': empresa,
        'meses_comparar': meses_comparar,
        'dados_meses': dados_meses,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'total_lucro': total_lucro,
        'media_receitas': media_receitas,
        'media_lucro': media_lucro,
        'melhor_mes': melhor_mes,
        'pior_mes': pior_mes,
    }
    return render(request, 'financeiro/comparativo.html', context)
