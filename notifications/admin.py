from django.contrib import admin
from django.utils.html import format_html
from .models import NotificacaoWhatsApp


@admin.register(NotificacaoWhatsApp)
class NotificacaoWhatsAppAdmin(admin.ModelAdmin):
    list_display = ['pessoa', 'tipo', 'telefone', 'status_envio', 'enviado_em', 'criado_em']
    list_filter = ['tipo', 'enviado', 'criado_em']
    search_fields = ['pessoa__nome', 'telefone', 'mensagem']
    readonly_fields = ['pessoa', 'checklist_item', 'tipo', 'mensagem', 'telefone',
                       'enviado', 'enviado_em', 'erro', 'criado_em']
    date_hierarchy = 'criado_em'

    def status_envio(self, obj):
        if obj.enviado:
            return format_html('<span style="color:green;">✓ Enviado</span>')
        elif obj.erro:
            return format_html('<span style="color:red;">✗ Erro</span>')
        return format_html('<span style="color:orange;">⏳ Pendente</span>')
    status_envio.short_description = 'Status'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
