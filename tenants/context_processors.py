def empresa_context(request):
    """
    Adiciona informações das empresas do usuário ao contexto de todos os templates.
    Inclui o papel (gestor/funcionário) por empresa.
    """
    empresas_usuario = []
    empresa_ativa = None
    is_gestor_ativa = False

    try:
        if hasattr(request, 'user') and request.user.is_authenticated:
            from core.models import Pessoa

            pessoa = Pessoa.objects.filter(user=request.user, ativo=True).first()
            if pessoa:
                todas_empresas = list(
                    pessoa.empresas.filter(ativo=True).order_by('nome')
                )
                for emp in todas_empresas:
                    papel = pessoa.get_papel_empresa(emp)
                    empresas_usuario.append({
                        'obj': emp,
                        'id': emp.id,
                        'nome': emp.nome,
                        'cor': emp.cor,
                        'papel': papel,
                        'is_gestor': papel == 'gestor',
                    })

                # Empresa ativa na sessão (None = todas)
                empresa_ativa_id = request.session.get('empresa_ativa_id')
                if empresa_ativa_id:
                    empresa_ativa = next(
                        (e for e in empresas_usuario if e['id'] == empresa_ativa_id),
                        None
                    )

                if empresa_ativa:
                    is_gestor_ativa = empresa_ativa['is_gestor']

    except Exception:
        pass

    # Contagem de notificações
    notif_count = 0
    try:
        if hasattr(request, 'user') and request.user.is_authenticated:
            from core.models import Pessoa
            p = Pessoa.objects.filter(user=request.user, ativo=True).first()
            if p:
                notif_count = p.notificacoes_inapp.filter(lida=False).count()
    except Exception:
        pass

    # Verificar se é gestor em alguma empresa
    is_gestor_alguma = is_gestor_ativa or any(e.get('is_gestor') for e in empresas_usuario)

    return {
        'empresas_usuario': empresas_usuario,
        'empresa_ativa': empresa_ativa,
        'is_gestor_ativa': is_gestor_ativa,
        'is_gestor_alguma': is_gestor_alguma,
        'notif_count': notif_count,
    }
