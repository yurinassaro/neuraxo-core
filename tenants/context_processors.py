def tenant_context(request):
    """
    Adiciona informações do tenant atual ao contexto de todos os templates.
    Usa django-tenants para obter o tenant atual da conexão.
    Inclui lista de tenants disponíveis para o usuário (acesso compartilhado).
    """
    from django.db import connection

    tenant_nome = None
    tenant_slug = None
    tenants_disponiveis = []

    try:
        # Obter o tenant da conexão atual (definido pelo TenantMainMiddleware)
        tenant = getattr(connection, 'tenant', None)

        if tenant and tenant.schema_name != 'public':
            tenant_nome = tenant.nome
            tenant_slug = tenant.schema_name

        # Carregar tenants disponíveis para o usuário (acesso compartilhado)
        if hasattr(request, 'user') and request.user.is_authenticated:
            from .models import AcessoCompartilhado, Domain

            # Tenant "casa" do usuário (onde tem Pessoa nativa)
            # + Tenants com acesso compartilhado
            acessos = AcessoCompartilhado.objects.filter(
                user=request.user,
                ativo=True,
            ).select_related('tenant_destino')

            for acesso in acessos:
                t = acesso.tenant_destino
                if not t.ativo or t.schema_name == 'public':
                    continue
                # Pegar domínio primário do tenant
                domain = Domain.objects.filter(
                    tenant=t, is_primary=True
                ).first()
                if not domain:
                    domain = Domain.objects.filter(tenant=t).first()
                if domain:
                    # Marcar se é o tenant atual
                    is_atual = (tenant and t.schema_name == tenant.schema_name)
                    tenants_disponiveis.append({
                        'nome': t.nome,
                        'slug': t.schema_name,
                        'domain': domain.domain,
                        'is_atual': is_atual,
                        'is_gestor': acesso.is_gestor,
                    })

    except Exception:
        pass

    return {
        'tenant_nome': tenant_nome,
        'tenant_slug': tenant_slug,
        'tenants_disponiveis': tenants_disponiveis,
    }
