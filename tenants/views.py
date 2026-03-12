from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django_tenants.utils import schema_context


@staff_member_required
def api_empresas_tenant(request, tenant_id):
    """API para carregar empresas de um tenant (usado no admin do AcessoCompartilhado)"""
    from .models import Client

    try:
        tenant = Client.objects.get(pk=tenant_id)
    except Client.DoesNotExist:
        return JsonResponse({'empresas': []})

    from core.models import Empresa

    with schema_context(tenant.schema_name):
        empresas = list(
            Empresa.objects.filter(ativo=True).order_by('nome').values('id', 'nome')
        )

    return JsonResponse({'empresas': empresas})
