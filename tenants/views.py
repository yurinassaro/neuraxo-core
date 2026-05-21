from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def trocar_empresa(request, empresa_id):
    """Troca a empresa ativa na sessão do usuário. 0 = todas."""
    if empresa_id == 0:
        # Limpar filtro - mostrar todas
        request.session.pop('empresa_ativa_id', None)
    else:
        from core.models import Pessoa
        pessoa = Pessoa.objects.filter(user=request.user, ativo=True).first()
        if pessoa and pessoa.empresas.filter(id=empresa_id, ativo=True).exists():
            request.session['empresa_ativa_id'] = empresa_id

    next_url = request.GET.get('next', request.META.get('HTTP_REFERER', '/'))
    return redirect(next_url)
