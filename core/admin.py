from django.contrib import admin
from .models import Empresa, Cargo, Pessoa, PessoaExterna, Cliente
from financeiro.models import ConfigMercadoPago, ContaBancaria


class ConfigMercadoPagoInline(admin.StackedInline):
    model = ConfigMercadoPago
    extra = 0
    max_num = 1
    fields = ['access_token', 'ativo', 'ultima_sync']
    readonly_fields = ['ultima_sync']
    verbose_name = 'Mercado Pago'
    verbose_name_plural = 'Mercado Pago'


class ContaBancariaInline(admin.TabularInline):
    model = ContaBancaria
    extra = 0
    fields = ['nome', 'banco', 'tipo_conta', 'agencia', 'numero_conta', 'saldo_inicial', 'cor', 'ativo']


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cor_display', 'ativo', 'mp_status', 'qtd_contas', 'qtd_pessoas', 'qtd_cargos', 'criado_em']
    list_filter = ['ativo']
    search_fields = ['nome', 'descricao']
    inlines = [ContaBancariaInline, ConfigMercadoPagoInline]

    def qtd_contas(self, obj):
        return obj.contas_bancarias.filter(ativo=True).count()
    qtd_contas.short_description = 'Contas'

    def mp_status(self, obj):
        try:
            config = obj.config_mp
            if config.ativo:
                return 'Ativo'
            return 'Inativo'
        except ConfigMercadoPago.DoesNotExist:
            return '-'
    mp_status.short_description = 'Mercado Pago'

    def cor_display(self, obj):
        return f'<span style="background-color:{obj.cor}; padding: 2px 10px; border-radius: 3px;">&nbsp;</span>'
    cor_display.short_description = 'Cor'
    cor_display.allow_tags = True

    def qtd_pessoas(self, obj):
        return obj.pessoas.filter(ativo=True).count()
    qtd_pessoas.short_description = 'Pessoas'

    def qtd_cargos(self, obj):
        return obj.cargos.filter(ativo=True).count()
    qtd_cargos.short_description = 'Cargos'


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'qtd_pessoas', 'ativo']
    list_filter = ['empresa', 'ativo']
    search_fields = ['nome', 'descricao', 'processos']

    def qtd_pessoas(self, obj):
        return obj.pessoas.filter(ativo=True).count()
    qtd_pessoas.short_description = 'Pessoas'


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'telefone', 'cargo', 'is_gestor', 'receber_lembretes', 'qtd_empresas_financeiro', 'ativo']
    list_filter = ['is_gestor', 'ativo', 'empresas', 'cargo', 'empresas_lembrete_financeiro']
    search_fields = ['nome', 'telefone', 'email']
    filter_horizontal = ['empresas', 'empresas_lembrete_financeiro']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'telefone', 'email', 'user')
        }),
        ('Vínculo', {
            'fields': ('empresas', 'cargo', 'is_gestor')
        }),
        ('Notificações', {
            'fields': ('receber_lembretes', 'horario_lembrete')
        }),
        ('Lembrete Financeiro', {
            'fields': ('empresas_lembrete_financeiro',),
            'description': 'Selecione as empresas das quais esta pessoa receberá lembrete de contas a pagar via WhatsApp'
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )

    def qtd_empresas_financeiro(self, obj):
        count = obj.empresas_lembrete_financeiro.count()
        return count if count > 0 else '-'
    qtd_empresas_financeiro.short_description = 'Lembrete Fin.'


@admin.register(PessoaExterna)
class PessoaExternaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'telefone', 'empresa_nome', 'criado_em']
    search_fields = ['nome', 'telefone', 'empresa_nome']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'cpf_cnpj', 'email', 'telefone', 'qtd_projetos', 'ativo', 'criado_em']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome', 'cpf_cnpj', 'email', 'telefone']
    readonly_fields = ['criado_em', 'atualizado_em']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'tipo', 'cpf_cnpj')
        }),
        ('Contato', {
            'fields': ('email', 'telefone', 'endereco')
        }),
        ('Outros', {
            'fields': ('observacoes', 'ativo')
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    def qtd_projetos(self, obj):
        total = obj.projetos.count()
        ativos = obj.get_projetos_ativos().count()
        if total == 0:
            return '-'
        return f'{ativos}/{total}'
    qtd_projetos.short_description = 'Projetos (ativos/total)'
