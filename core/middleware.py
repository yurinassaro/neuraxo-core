import logging
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


class FriendlyErrorMiddleware:
    """Captura exceções não tratadas em views e mostra mensagem amigável."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # Não interceptar no admin
        if request.path.startswith('/admin/'):
            return None

        # Http404 e PermissionDenied são controle de fluxo, não erro interno.
        # Deixar o Django tratá-los com os status corretos (404 / 403) — caso
        # contrário um IDOR barrado por Http404 viraria 400 e mascararia a causa.
        if isinstance(exception, (Http404, PermissionDenied)):
            return None

        # Erro interno de verdade: logar com stack completo (logger.exception
        # captura o traceback do contexto atual).
        logger.exception('Erro na view %s', request.path)

        # Requisições AJAX/JSON retornam JSON — mensagem genérica, NUNCA str(e)
        # (não vazar detalhe interno/PII ao cliente).
        is_ajax = (
            request.headers.get('Content-Type') == 'application/json'
            or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        )
        if is_ajax:
            return JsonResponse({'error': 'Ocorreu um erro ao processar a requisição.'}, status=500)

        messages.error(request, 'Ocorreu um erro ao processar a requisição.')

        referer = request.META.get('HTTP_REFERER')
        if referer and request.method == 'POST':
            return redirect(referer)

        return redirect('dashboard')
