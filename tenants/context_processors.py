def tenant_context(request):
    """
    Adiciona informações do tenant atual ao contexto de todos os templates.
    Usa django-tenants para obter o tenant atual da conexão.
    """
    from django.db import connection

    tenant_nome = None
    tenant_slug = None

    try:
        # Obter o tenant da conexão atual (definido pelo TenantMainMiddleware)
        tenant = getattr(connection, 'tenant', None)

        if tenant and tenant.schema_name != 'public':
            tenant_nome = tenant.nome
            tenant_slug = tenant.schema_name

    except Exception:
        pass

    return {
        'tenant_nome': tenant_nome,
        'tenant_slug': tenant_slug,
    }
