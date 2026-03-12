from django.contrib import admin
from django import forms
from django.db import connection
from django.utils.html import format_html
from django_tenants.admin import TenantAdminMixin
from django_tenants.utils import schema_context
from .models import Client, Domain, ProjetoTemplateGlobal, EtapaTemplateGlobal, AcessoCompartilhado


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 1


@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('nome', 'schema_name', 'ativo', 'criado_em')
    inlines = [DomainInline]

    def has_module_permission(self, request):
        return connection.schema_name == 'public'

    def has_view_permission(self, request, obj=None):
        return connection.schema_name == 'public'

    def has_add_permission(self, request):
        return connection.schema_name == 'public'

    def has_change_permission(self, request, obj=None):
        return connection.schema_name == 'public'

    def has_delete_permission(self, request, obj=None):
        return connection.schema_name == 'public'


# ============================================
# TEMPLATES DE PROJETO GLOBAIS (gerenciados no public)
# ============================================

class EtapaTemplateGlobalInline(admin.TabularInline):
    model = EtapaTemplateGlobal
    extra = 1
    fields = ['ordem', 'titulo', 'descricao', 'tempo_estimado']


@admin.register(ProjetoTemplateGlobal)
class ProjetoTemplateGlobalAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'get_total_etapas', 'get_tenants_list', 'cor', 'ativo')
    list_filter = ('ativo', 'tenants')
    search_fields = ('titulo', 'descricao')
    filter_horizontal = ('tenants',)
    inlines = [EtapaTemplateGlobalInline]

    fieldsets = (
        ('Informações do Template', {
            'fields': ('titulo', 'descricao', 'cor')
        }),
        ('Tenants Vinculados', {
            'fields': ('tenants',),
            'description': 'Selecione os tenants que poderão usar este template de projeto.'
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )

    def get_total_etapas(self, obj):
        return obj.etapas.count()
    get_total_etapas.short_description = 'Etapas'

    def get_tenants_list(self, obj):
        tenants = obj.tenants.exclude(schema_name='public')
        if not tenants:
            return "-"
        return ", ".join([t.nome for t in tenants[:3]]) + ("..." if tenants.count() > 3 else "")
    get_tenants_list.short_description = 'Tenants'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "tenants":
            kwargs["queryset"] = Client.objects.exclude(schema_name='public').order_by('nome')
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def has_module_permission(self, request):
        return connection.schema_name == 'public'

    def has_view_permission(self, request, obj=None):
        return connection.schema_name == 'public'

    def has_add_permission(self, request):
        return connection.schema_name == 'public'

    def has_change_permission(self, request, obj=None):
        return connection.schema_name == 'public'

    def has_delete_permission(self, request, obj=None):
        return connection.schema_name == 'public'


# ============================================
# ACESSO COMPARTILHADO (gerenciado no public)
# ============================================

class AcessoCompartilhadoForm(forms.ModelForm):
    """Form customizado para selecionar empresas do tenant destino"""
    empresas_escolhidas = forms.MultipleChoiceField(
        choices=[],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Empresas Permitidas',
        help_text='Selecione as empresas que o usuário poderá acessar no tenant destino',
    )

    class Meta:
        model = AcessoCompartilhado
        fields = ['user', 'tenant_destino', 'is_gestor', 'ativo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.tenant_destino_id:
            self._carregar_empresas(self.instance.tenant_destino)
            self.initial['empresas_escolhidas'] = [
                str(eid) for eid in (self.instance.empresas_ids or [])
            ]
        elif self.data and self.data.get('tenant_destino'):
            try:
                tenant = Client.objects.get(pk=self.data['tenant_destino'])
                self._carregar_empresas(tenant)
            except Client.DoesNotExist:
                pass

    def _carregar_empresas(self, tenant):
        from core.models import Empresa
        with schema_context(tenant.schema_name):
            empresas = Empresa.objects.filter(ativo=True).order_by('nome')
            self.fields['empresas_escolhidas'].choices = [
                (str(e.id), e.nome) for e in empresas
            ]

    def clean(self):
        cleaned_data = super().clean()
        empresas = cleaned_data.get('empresas_escolhidas', [])
        cleaned_data['empresas_ids'] = [int(eid) for eid in empresas]
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.empresas_ids = self.cleaned_data.get('empresas_ids', [])
        if commit:
            instance.save()
        return instance


@admin.register(AcessoCompartilhado)
class AcessoCompartilhadoAdmin(admin.ModelAdmin):
    form = AcessoCompartilhadoForm
    list_display = ('user', 'tenant_destino', 'papel_display', 'empresas_display', 'ativo', 'criado_em')
    list_filter = ('ativo', 'is_gestor', 'tenant_destino')
    search_fields = ('user__username', 'tenant_destino__nome')

    def papel_display(self, obj):
        if obj.is_gestor:
            return format_html('<span style="color: #059669; font-weight: bold;">Gestor</span>')
        return format_html('<span style="color: #6366f1;">Funcionário</span>')
    papel_display.short_description = 'Papel'

    def empresas_display(self, obj):
        return obj.get_empresas_display()
    empresas_display.short_description = 'Empresas'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'tenant_destino':
            kwargs['queryset'] = Client.objects.exclude(schema_name='public').order_by('nome')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_module_permission(self, request):
        return connection.schema_name == 'public'

    def has_view_permission(self, request, obj=None):
        return connection.schema_name == 'public'

    def has_add_permission(self, request):
        return connection.schema_name == 'public'

    def has_change_permission(self, request, obj=None):
        return connection.schema_name == 'public'

    def has_delete_permission(self, request, obj=None):
        return connection.schema_name == 'public'
