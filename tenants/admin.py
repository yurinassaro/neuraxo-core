from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nome', 'schema_name', 'admin_user', 'ativo', 'criado_em')
    list_filter = ('ativo',)
    search_fields = ('nome', 'schema_name')
