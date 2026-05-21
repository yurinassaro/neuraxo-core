import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from core.models import Empresa, Pessoa
from .models import GatewayPagamento
from checklists.views import get_pessoa_or_redirect, get_empresas_filtradas


@login_required
def integracoes(request):
    """Página de integrações - cards dos gateways disponíveis"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return redirect('dashboard')

    empresas = get_empresas_filtradas(pessoa, request)

    # Buscar gateways configurados para as empresas do usuário
    gateways = GatewayPagamento.objects.filter(empresa__in=empresas).select_related('empresa')
    gateways_por_empresa = {g.empresa_id: g for g in gateways}

    context = {
        'pessoa': pessoa,
        'empresas': empresas,
        'gateways_por_empresa': gateways_por_empresa,
    }
    return render(request, 'financeiro/integracoes.html', context)


@login_required
@require_POST
def conectar_gateway(request):
    """Conecta um gateway de pagamento a uma empresa"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        messages.error(request, 'Apenas gestores podem configurar integrações.')
        return redirect('integracoes')

    empresa_id = request.POST.get('empresa')
    gateway_tipo = request.POST.get('gateway')

    empresa = get_object_or_404(Empresa, id=empresa_id)
    if empresa not in pessoa.empresas.all():
        messages.error(request, 'Sem permissão.')
        return redirect('integracoes')

    # Verificar se já existe gateway para esta empresa
    gw, created = GatewayPagamento.objects.get_or_create(
        empresa=empresa,
        defaults={'gateway': gateway_tipo, 'status': 'pendente'}
    )
    if not created:
        gw.gateway = gateway_tipo
        gw.status = 'pendente'
        gw.credentials_encrypted = ''
        gw.save()

    credentials = {}

    if gateway_tipo == 'mercadopago':
        access_token = request.POST.get('access_token', '').strip()
        if not access_token:
            messages.error(request, 'Informe o Access Token do Mercado Pago.')
            return redirect('integracoes')
        credentials = {'access_token': access_token}

        # Testar conexão
        try:
            r = requests.get(
                'https://api.mercadopago.com/v1/payment_methods',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10
            )
            if r.status_code == 200:
                gw.status = 'ativo'
            else:
                gw.status = 'erro'
                messages.warning(request, f'Token informado retornou erro ({r.status_code}). Verifique e tente novamente.')
        except Exception:
            gw.status = 'erro'
            messages.warning(request, 'Não foi possível validar o token. Salvo como pendente.')

    elif gateway_tipo == 'asaas':
        api_key = request.POST.get('api_key', '').strip()
        if not api_key:
            messages.error(request, 'Informe a API Key do Asaas.')
            return redirect('integracoes')

        sandbox = request.POST.get('sandbox') == 'on'
        credentials = {'api_key': api_key}
        gw.sandbox = sandbox

        # Testar conexão
        base_url = 'https://sandbox.asaas.com/api/v3' if sandbox else 'https://api.asaas.com/v3'
        try:
            r = requests.get(
                f'{base_url}/finance/getCurrentBalance',
                headers={'access_token': api_key},
                timeout=10
            )
            if r.status_code == 200:
                gw.status = 'ativo'
                saldo = r.json().get('balance', 0)
                messages.success(request, f'Asaas conectado! Saldo atual: R$ {saldo:,.2f}')
            else:
                gw.status = 'erro'
                messages.warning(request, f'API Key retornou erro ({r.status_code}).')
        except Exception:
            gw.status = 'erro'
            messages.warning(request, 'Não foi possível validar a API Key.')

    elif gateway_tipo == 'efi':
        client_id = request.POST.get('client_id', '').strip()
        client_secret = request.POST.get('client_secret', '').strip()
        if not client_id or not client_secret:
            messages.error(request, 'Informe Client ID e Client Secret da EFI.')
            return redirect('integracoes')

        sandbox = request.POST.get('sandbox') == 'on'
        credentials = {'client_id': client_id, 'client_secret': client_secret}
        gw.sandbox = sandbox

        # Certificado (upload opcional neste momento)
        cert_file = request.FILES.get('certificado')
        if cert_file:
            import os
            cert_dir = os.path.join('media', 'certificates', str(empresa.id))
            os.makedirs(cert_dir, exist_ok=True)
            cert_path = os.path.join(cert_dir, 'certificado.pem')
            with open(cert_path, 'wb') as f:
                for chunk in cert_file.chunks():
                    f.write(chunk)
            credentials['cert_path'] = cert_path

        gw.status = 'pendente'
        messages.success(request, 'EFI configurada. Faça o teste de conexão para validar.')

    gw.set_credentials(credentials)
    gw.save()

    if gw.status == 'ativo':
        messages.success(request, f'{gw.get_gateway_display()} conectado com sucesso!')

    return redirect('integracoes')


@login_required
@require_POST
def desconectar_gateway(request, empresa_id):
    """Desconecta o gateway de uma empresa"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa or not pessoa.eh_gestor:
        return redirect('integracoes')

    gw = get_object_or_404(GatewayPagamento, empresa_id=empresa_id)
    nome = gw.get_gateway_display()
    gw.delete()
    messages.success(request, f'{nome} desconectado de {gw.empresa.nome}.')
    return redirect('integracoes')


@login_required
@require_POST
def testar_gateway(request, empresa_id):
    """Testa a conexão do gateway (AJAX)"""
    pessoa = get_pessoa_or_redirect(request)
    if not pessoa:
        return JsonResponse({'ok': False, 'msg': 'Sem permissão'})

    gw = get_object_or_404(GatewayPagamento, empresa_id=empresa_id)
    creds = gw.get_credentials()

    ok = False
    msg = 'Erro desconhecido'

    try:
        if gw.gateway == 'mercadopago':
            r = requests.get(
                'https://api.mercadopago.com/v1/payment_methods',
                headers={'Authorization': f'Bearer {creds.get("access_token", "")}'},
                timeout=10
            )
            ok = r.status_code == 200
            msg = 'Conexão OK' if ok else f'Erro {r.status_code}'

        elif gw.gateway == 'asaas':
            base_url = 'https://sandbox.asaas.com/api/v3' if gw.sandbox else 'https://api.asaas.com/v3'
            r = requests.get(
                f'{base_url}/finance/getCurrentBalance',
                headers={'access_token': creds.get('api_key', '')},
                timeout=10
            )
            ok = r.status_code == 200
            if ok:
                saldo = r.json().get('balance', 0)
                msg = f'Conexão OK — Saldo: R$ {saldo:,.2f}'
            else:
                msg = f'Erro {r.status_code}'

        elif gw.gateway == 'efi':
            msg = 'EFI: teste de conexão requer certificado. Configure via painel EFI.'
            ok = bool(creds.get('client_id'))

    except Exception as e:
        msg = f'Erro de conexão: {str(e)[:100]}'

    if ok:
        gw.status = 'ativo'
    else:
        gw.status = 'erro'
    gw.save()

    return JsonResponse({'ok': ok, 'msg': msg, 'status': gw.status})
