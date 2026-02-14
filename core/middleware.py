import logging
import traceback
from django.contrib import messages
from django.http import JsonResponse
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

        logger.error(
            'Erro na view %s: %s\n%s',
            request.path,
            exception,
            traceback.format_exc(),
        )

        error_msg = str(exception)
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + '...'

        # Requisições AJAX/JSON retornam JSON
        is_ajax = (
            request.headers.get('Content-Type') == 'application/json'
            or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        )
        if is_ajax:
            return JsonResponse({'error': error_msg}, status=400)

        messages.error(request, f'Ocorreu um erro: {error_msg}')

        referer = request.META.get('HTTP_REFERER')
        if referer and request.method == 'POST':
            return redirect(referer)

        return redirect('dashboard')
