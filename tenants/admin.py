from django.contrib import admin
from django.db import connection
from django_tenants.admin import TenantAdminMixin
from .models import Client, Domain, ProjetoTemplateGlobal, EtapaTemplateGlobal


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
        """Mostra lista de tenants vinculados na listagem"""
        tenants = obj.tenants.exclude(schema_name='public')
        if not tenants:
            return "-"
        return ", ".join([t.nome for t in tenants[:3]]) + ("..." if tenants.count() > 3 else "")
    get_tenants_list.short_description = 'Tenants'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Filtra tenants para não mostrar o public"""
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
