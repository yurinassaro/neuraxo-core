import logging
from django.db import connection

logger = logging.getLogger(__name__)


class AcessoCompartilhadoMiddleware:
    """
    Middleware que sincroniza Pessoa para usuários com acesso compartilhado.
    Quando um usuário acessa um tenant onde não é "nativo", mas tem
    AcessoCompartilhado, cria/atualiza a Pessoa com as empresas permitidas.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Só processar se o usuário está autenticado e estamos em um tenant
        if (
            hasattr(request, 'user')
            and request.user.is_authenticated
            and hasattr(connection, 'tenant')
            and connection.tenant.schema_name != 'public'
        ):
            self._sincronizar_acesso(request)

        return self.get_response(request)

    def _sincronizar_acesso(self, request):
        """Verifica e sincroniza acesso compartilhado se necessário"""
        # Usar cache na sessão para não consultar a cada request
        cache_key = f'acesso_sync_{connection.tenant.schema_name}'
        if request.session.get(cache_key):
            return

        try:
            from .models import AcessoCompartilhado

            acesso = AcessoCompartilhado.objects.filter(
                user=request.user,
                tenant_destino=connection.tenant,
                ativo=True,
            ).first()

            if acesso:
                acesso.sincronizar_pessoa()
                # Marcar na sessão que já sincronizou (evita repetir)
                request.session[cache_key] = True

        except Exception as e:
            logger.warning(f"Erro ao sincronizar acesso compartilhado: {e}")
