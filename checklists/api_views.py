"""
API Views para integração WhatsApp via WAPI
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import ChecklistItem, StatusItem
from core.models import Pessoa
from notifications.wapi import WAPIClient, montar_mensagem_confirmacao


@csrf_exempt
@require_http_methods(["POST"])
def webhook_wapi(request):
    """
    Webhook para receber mensagens do WAPI
    Comandos aceitos:
    - "tarefas" ou "minhas tarefas" - lista tarefas pendentes
    - "1", "2", etc - marca tarefa correspondente como concluída
    - "ajuda" - mostra comandos disponíveis
    """
    try:
        data = json.loads(request.body)
        mensagem = data.get('message', {})
        texto = mensagem.get('body', '').strip().lower()
        telefone = mensagem.get('from', '').replace('@s.whatsapp.net', '')

        if not texto or not telefone:
            return JsonResponse({'status': 'ignored'})

        # Busca pessoa pelo telefone
        pessoa = None
        for p in Pessoa.objects.filter(ativo=True):
            if p.telefone_formatado() == telefone or telefone.endswith(p.telefone_formatado()[-9:]):
                pessoa = p
                break

        if not pessoa:
            return JsonResponse({'status': 'pessoa_not_found'})

        client = WAPIClient()
        resposta = None

        # Comandos
        if texto in ['tarefas', 'minhas tarefas', 'pendentes']:
            resposta = processar_comando_tarefas(pessoa)

        elif texto in ['ajuda', 'help', 'comandos']:
            resposta = processar_comando_ajuda()

        elif texto.isdigit():
            resposta = processar_comando_concluir(pessoa, int(texto))

        elif texto.startswith('concluir ') and texto[9:].isdigit():
            resposta = processar_comando_concluir(pessoa, int(texto[9:]))

        if resposta and client.esta_configurado():
            client.enviar_mensagem(telefone, resposta)

        return JsonResponse({'status': 'ok', 'resposta': resposta})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def processar_comando_tarefas(pessoa: Pessoa) -> str:
    """Retorna lista de tarefas pendentes"""
    hoje = timezone.localdate()
    items = ChecklistItem.objects.filter(
        responsavel=pessoa,
        data_referencia=hoje,
        status__in=[StatusItem.PENDENTE, StatusItem.EM_ANDAMENTO, StatusItem.ATRASADO]
    ).select_related('template')

    if not items:
        return f"*{pessoa.nome.split()[0]}*, você não tem tarefas pendentes hoje! \n\n_NeuraxoCheck_"

    linhas = [
        f"*{pessoa.nome.split()[0]}*, suas tarefas de hoje:",
        ""
    ]

    for i, item in enumerate(items, 1):
        status = ""
        if item.status == StatusItem.ATRASADO:
            status = " (ATRASADA)"
        elif item.status == StatusItem.EM_ANDAMENTO:
            status = " (em andamento)"

        linhas.append(f"*{i}.* {item.template.titulo}{status}")

    linhas.extend([
        "",
        "Para concluir, responda com o número da tarefa.",
        "Ex: *1* para concluir a primeira",
        "",
        "_NeuraxoCheck_"
    ])

    return "\n".join(linhas)


def processar_comando_ajuda() -> str:
    """Retorna texto de ajuda"""
    return """*Comandos disponíveis:*

*tarefas* - Ver suas tarefas pendentes
*1*, *2*, etc - Marcar tarefa como concluída
*ajuda* - Ver este menu

_NeuraxoCheck_"""


def processar_comando_concluir(pessoa: Pessoa, numero: int) -> str:
    """Marca uma tarefa como concluída pelo número"""
    hoje = timezone.localdate()
    items = list(ChecklistItem.objects.filter(
        responsavel=pessoa,
        data_referencia=hoje,
        status__in=[StatusItem.PENDENTE, StatusItem.EM_ANDAMENTO, StatusItem.ATRASADO]
    ).select_related('template').order_by('id'))

    if numero < 1 or numero > len(items):
        return f"Número inválido. Você tem {len(items)} tarefa(s) pendente(s). Responda *tarefas* para ver a lista."

    item = items[numero - 1]
    item.marcar_concluido()

    return montar_mensagem_confirmacao(pessoa, item)


@csrf_exempt
@require_http_methods(["GET"])
def tarefas_pessoa(request, telefone):
    """API para buscar tarefas de uma pessoa por telefone"""
    pessoa = None
    for p in Pessoa.objects.filter(ativo=True):
        if p.telefone_formatado() == telefone or telefone.endswith(p.telefone_formatado()[-9:]):
            pessoa = p
            break

    if not pessoa:
        return JsonResponse({'error': 'Pessoa não encontrada'}, status=404)

    hoje = timezone.localdate()
    items = ChecklistItem.objects.filter(
        responsavel=pessoa,
        data_referencia=hoje
    ).select_related('template', 'template__workspace')

    return JsonResponse({
        'pessoa': pessoa.nome,
        'data': str(hoje),
        'tarefas': [
            {
                'id': item.id,
                'titulo': item.template.titulo,
                'workspace': item.template.workspace.nome,
                'status': item.status,
                'prioridade': item.template.prioridade,
            }
            for item in items
        ]
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_marcar_concluido(request, item_id):
    """API para marcar item como concluído"""
    try:
        item = ChecklistItem.objects.get(id=item_id)
        item.marcar_concluido()
        return JsonResponse({'status': 'ok', 'message': 'Tarefa concluída'})
    except ChecklistItem.DoesNotExist:
        return JsonResponse({'error': 'Item não encontrado'}, status=404)
