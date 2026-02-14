from django.contrib import admin
from django.utils.html import format_html
from .models import MetaEmpresa, CategoriaLancamento, Lancamento, ConfigMercadoPago, ContaBancaria, PrestacaoConta, ContaPagar, ContaPagarItem


@admin.register(MetaEmpresa)
class MetaEmpresaAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'mes_ano', 'valor_meta_fmt', 'realizado_fmt', 'progresso_badge', 'dias_uteis']
    list_filter = ['empresa', 'ano']
    list_editable = ['dias_uteis']

    def mes_ano(self, obj):
        return f"{obj.mes:02d}/{obj.ano}"
    mes_ano.short_description = 'Período'

    def valor_meta_fmt(self, obj):
        return f"R$ {obj.valor_meta:,.2f}"
    valor_meta_fmt.short_description = 'Meta'

    def realizado_fmt(self, obj):
        return f"R$ {obj.get_realizado_mes():,.2f}"
    realizado_fmt.short_description = 'Realizado'

    def progresso_badge(self, obj):
        p = obj.get_progresso()
        cor = '#28a745' if p >= 100 else '#ffc107' if p >= 70 else '#dc3545'
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}%</span>', cor, p
        )
    progresso_badge.short_description = 'Progresso'


@admin.register(CategoriaLancamento)
class CategoriaLancamentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'empresa', 'cor_badge', 'ativo', 'ordem']
    list_filter = ['tipo', 'empresa', 'ativo']
    list_editable = ['ordem', 'ativo']

    def cor_badge(self, obj):
        return format_html(
            '<span style="background:{}; padding:2px 12px; border-radius:3px; color:white;">{}</span>',
            obj.cor, obj.cor
        )
    cor_badge.short_description = 'Cor'


class PrestacaoContaInline(admin.TabularInline):
    model = PrestacaoConta
    extra = 0
    fields = ['descricao', 'categoria', 'valor']


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = ['data', 'empresa', 'tipo_badge', 'categoria', 'descricao', 'valor_fmt', 'pessoa', 'projeto']
    list_filter = ['tipo', 'empresa', 'categoria', 'data', 'projeto']
    search_fields = ['descricao', 'observacao']
    date_hierarchy = 'data'
    raw_id_fields = ['pessoa', 'criado_por']
    inlines = [PrestacaoContaInline]

    def tipo_badge(self, obj):
        cor = '#28a745' if obj.tipo == 'entrada' else '#dc3545'
        sinal = '+' if obj.tipo == 'entrada' else '-'
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>', cor, sinal
        )
    tipo_badge.short_description = 'Tipo'

    def valor_fmt(self, obj):
        cor = '#28a745' if obj.tipo == 'entrada' else '#dc3545'
        return format_html(
            '<span style="color:{};">R$ {:,.2f}</span>', cor, obj.valor
        )
    valor_fmt.short_description = 'Valor'


@admin.register(ConfigMercadoPago)
class ConfigMercadoPagoAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'ativo_badge', 'token_mascarado', 'ultima_sync_fmt']
    list_filter = ['ativo']
    list_editable = []
    readonly_fields = ['ultima_sync', 'criado_em', 'atualizado_em']
    fieldsets = (
        ('Empresa', {
            'fields': ('empresa',),
        }),
        ('Credenciais', {
            'fields': ('access_token',),
            'description': 'Obtenha o Access Token em: Mercado Pago > Seu negócio > Configurações > Gestão e Administração > Credenciais',
        }),
        ('Status', {
            'fields': ('ativo', 'ultima_sync', 'criado_em', 'atualizado_em'),
        }),
    )

    def ativo_badge(self, obj):
        if obj.ativo:
            return format_html('<span style="color:#28a745; font-weight:bold;">Ativo</span>')
        return format_html('<span style="color:#dc3545;">Inativo</span>')
    ativo_badge.short_description = 'Status'

    def token_mascarado(self, obj):
        if obj.access_token:
            return f'****{obj.access_token[-8:]}'
        return '-'
    token_mascarado.short_description = 'Token'

    def ultima_sync_fmt(self, obj):
        if obj.ultima_sync:
            return obj.ultima_sync.strftime('%d/%m/%Y %H:%M')
        return 'Nunca'
    ultima_sync_fmt.short_description = 'Última Sync'


@admin.register(ContaBancaria)
class ContaBancariaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'banco', 'tipo_conta', 'agencia', 'numero_conta',
                    'saldo_inicial_fmt', 'saldo_atual_fmt', 'cor_badge', 'ativo']
    list_filter = ['empresa', 'tipo_conta', 'ativo']
    search_fields = ['nome', 'banco']
    list_editable = ['ativo']

    def saldo_inicial_fmt(self, obj):
        return f'R$ {obj.saldo_inicial:,.2f}'
    saldo_inicial_fmt.short_description = 'Saldo Inicial'

    def saldo_atual_fmt(self, obj):
        saldo = obj.get_saldo()
        cor = '#28a745' if saldo >= 0 else '#dc3545'
        return format_html('<span style="color:{}; font-weight:bold;">R$ {:,.2f}</span>', cor, saldo)
    saldo_atual_fmt.short_description = 'Saldo Atual'

    def cor_badge(self, obj):
        return format_html(
            '<span style="background:{}; padding:2px 12px; border-radius:3px; color:white;">{}</span>',
            obj.cor, obj.cor
        )
    cor_badge.short_description = 'Cor'


class ContaPagarItemInline(admin.TabularInline):
    model = ContaPagarItem
    extra = 0
    fields = ['mes', 'ano', 'valor', 'data_vencimento', 'data_execucao', 'pago', 'pago_em']
    readonly_fields = ['pago_em']


@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ['descricao', 'empresa', 'valor_fmt', 'recorrencia', 'dia_vencimento', 'dia_execucao', 'ativo']
    list_filter = ['empresa', 'recorrencia', 'ativo']
    search_fields = ['descricao']
    list_editable = ['ativo']
    inlines = [ContaPagarItemInline]

    def valor_fmt(self, obj):
        return f'R$ {obj.valor:,.2f}'
    valor_fmt.short_description = 'Valor'


@admin.register(ContaPagarItem)
class ContaPagarItemAdmin(admin.ModelAdmin):
    list_display = ['conta_pagar', 'mes_ano', 'valor_fmt', 'data_vencimento', 'data_execucao', 'pago_badge']
    list_filter = ['pago', 'ano', 'mes']

    def mes_ano(self, obj):
        return f'{obj.mes:02d}/{obj.ano}'
    mes_ano.short_description = 'Período'

    def valor_fmt(self, obj):
        return f'R$ {obj.valor:,.2f}'
    valor_fmt.short_description = 'Valor'

    def pago_badge(self, obj):
        if obj.pago:
            return format_html('<span style="color:#28a745; font-weight:bold;">Pago</span>')
        return format_html('<span style="color:#dc3545;">Pendente</span>')
    pago_badge.short_description = 'Status'
