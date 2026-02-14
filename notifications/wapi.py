"""
Cliente WAPI para envio de mensagens WhatsApp
"""
import requests
from django.conf import settings
from django.utils import timezone
from .models import NotificacaoWhatsApp, TipoNotificacao
from core.models import Pessoa
from checklists.models import ChecklistItem, StatusItem


class WAPIClient:
    """Cliente para API W-API (w-api.app)"""

    BASE_URL = 'https://api.w-api.app/v1'

    def __init__(self):
        self.token = settings.WAPI_TOKEN
        self.instance = settings.WAPI_INSTANCE

    def esta_configurado(self) -> bool:
        """Verifica se WAPI está configurado"""
        return bool(self.token and self.instance)

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
        }

    def verificar_status(self) -> dict:
        """Verifica status da instância"""
        if not self.esta_configurado():
            return {'success': False, 'error': 'WAPI não configurado'}
        try:
            response = requests.get(
                f"{self.BASE_URL}/instance/status-instance",
                params={'instanceId': self.instance},
                headers=self._headers(),
                timeout=30
            )
            if response.ok:
                data = response.json()
                return {'success': True, 'connected': data.get('connected', False), 'data': data}
            return {'success': False, 'error': response.text}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}

    def enviar_mensagem(self, telefone: str, mensagem: str, delay: int = 5) -> dict:
        """Envia mensagem de texto via W-API"""
        if not self.esta_configurado():
            return {'success': False, 'error': 'WAPI não configurado'}

        try:
            response = requests.post(
                f"{self.BASE_URL}/message/send-text?instanceId={self.instance}",
                json={
                    'phone': telefone,
                    'message': mensagem,
                    'delayMessage': delay,
                    'disableTestMsg': True,
                },
                headers=self._headers(),
                timeout=30
            )

            if response.ok:
                return {'success': True, 'response': response.json()}
            return {'success': False, 'error': response.text}

        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}


def montar_mensagem_lembrete(pessoa: Pessoa, items: list, demandas_hoje=None, demandas_amanha=None, contas_pagar=None) -> str:
    """Monta mensagem de lembrete com tarefas, demandas e contas a pagar"""
    demandas_hoje = demandas_hoje or []
    demandas_amanha = demandas_amanha or []
    contas_pagar = contas_pagar or []

    if not items and not demandas_hoje and not demandas_amanha and not contas_pagar:
        return ""

    linhas = [f"📋 *Olá, {pessoa.nome.split()[0]}!*", ""]

    if items:
        linhas.append(f"*{len(items)} tarefa(s) para hoje:*")
        for i, item in enumerate(items, 1):
            prioridade = "🔴" if item.template.prioridade == 3 else "🟡" if item.template.prioridade == 2 else "🟢"
            linhas.append(f"{i}. {prioridade} {item.template.titulo}")
        linhas.append("")

    if demandas_hoje:
        linhas.append(f"⚠️ *{len(demandas_hoje)} demanda(s) vencendo HOJE:*")
        for d in demandas_hoje:
            linhas.append(f"• 🔴 {d.titulo} ({d.empresa.nome})")
        linhas.append("")

    if demandas_amanha:
        linhas.append(f"📅 *{len(demandas_amanha)} demanda(s) vencendo AMANHÃ:*")
        for d in demandas_amanha:
            linhas.append(f"• 🟡 {d.titulo} ({d.empresa.nome})")
        linhas.append("")

    if contas_pagar:
        total = sum(c.valor for c in contas_pagar)
        linhas.append(f"💰 *{len(contas_pagar)} conta(s) a pagar hoje (R$ {total:,.2f}):*")
        for c in contas_pagar:
            linhas.append(f"• {c.conta_pagar.descricao} - R$ {c.valor:,.2f} (venc. {c.data_vencimento.strftime('%d/%m')})")
        linhas.append("")

    linhas.extend([
        "✅ Acesse o sistema para detalhes",
        "",
        "*Neuraxo-Check - Mensagem Automática*"
    ])

    return "\n".join(linhas)


def montar_mensagem_cobranca(pessoa: Pessoa, items: list) -> str:
    """Monta mensagem de cobrança (tarefas não concluídas)"""
    if not items:
        return ""

    linhas = [
        f"⚠️ *Atenção, {pessoa.nome.split()[0]}!*",
        "",
        f"Você tem *{len(items)} tarefa(s) pendente(s)*:",
        ""
    ]

    for i, item in enumerate(items, 1):
        status = "⏰ Atrasada" if item.status == StatusItem.ATRASADO else "⏳ Pendente"
        linhas.append(f"{i}. {item.template.titulo} - {status}")

    linhas.extend([
        "",
        "📌 Por favor, finalize suas tarefas.",
        "",
        "*Neuraxo-Check - Mensagem Automática*"
    ])

    return "\n".join(linhas)


def montar_mensagem_confirmacao(pessoa: Pessoa, item: ChecklistItem) -> str:
    """Monta mensagem de confirmação de conclusão"""
    return f"""✅ *Tarefa concluída!*

{item.template.titulo}

Obrigado, {pessoa.nome.split()[0]}! 🎉

*Neuraxo-Check - Mensagem Automática*"""


def enviar_lembrete_pessoa(pessoa: Pessoa, items: list) -> NotificacaoWhatsApp:
    """Envia lembrete para uma pessoa"""
    if not pessoa.receber_lembretes or not items:
        return None

    mensagem = montar_mensagem_lembrete(pessoa, items)
    telefone = pessoa.telefone_formatado()

    notificacao = NotificacaoWhatsApp.objects.create(
        pessoa=pessoa,
        tipo=TipoNotificacao.LEMBRETE,
        mensagem=mensagem,
        telefone=telefone
    )

    client = WAPIClient()
    resultado = client.enviar_mensagem(telefone, mensagem)

    if resultado['success']:
        notificacao.enviado = True
        notificacao.enviado_em = timezone.now()
    else:
        notificacao.erro = resultado.get('error', 'Erro desconhecido')

    notificacao.save()

    # Marca itens como lembrete enviado
    for item in items:
        item.lembrete_enviado = True
        item.save()

    return notificacao


def enviar_cobranca_pessoa(pessoa: Pessoa, items: list) -> NotificacaoWhatsApp:
    """Envia cobrança para uma pessoa"""
    if not pessoa.receber_lembretes or not items:
        return None

    mensagem = montar_mensagem_cobranca(pessoa, items)
    telefone = pessoa.telefone_formatado()

    notificacao = NotificacaoWhatsApp.objects.create(
        pessoa=pessoa,
        tipo=TipoNotificacao.COBRANCA,
        mensagem=mensagem,
        telefone=telefone
    )

    client = WAPIClient()
    resultado = client.enviar_mensagem(telefone, mensagem)

    if resultado['success']:
        notificacao.enviado = True
        notificacao.enviado_em = timezone.now()
    else:
        notificacao.erro = resultado.get('error', 'Erro desconhecido')

    notificacao.save()

    # Marca itens como cobrança enviada
    for item in items:
        item.cobranca_enviada = True
        item.save()

    return notificacao


def processar_lembretes_diarios():
    """Processa e envia lembretes do dia (tarefas + demandas + contas a pagar)"""
    from datetime import timedelta
    from checklists.models import ChecklistItem, StatusItem, Demanda, StatusDemanda
    from financeiro.models import ContaPagarItem

    hoje = timezone.localdate()
    amanha = hoje + timedelta(days=1)
    agora = timezone.now()
    resultado = {'enviados': 0, 'erros': 0}

    # Tarefas do dia por pessoa
    pessoas_items = {}
    items = ChecklistItem.objects.filter(
        data_referencia=hoje,
        status__in=[StatusItem.PENDENTE, StatusItem.EM_ANDAMENTO],
        lembrete_enviado=False,
        template__enviar_lembrete=True
    ).select_related('responsavel', 'template')

    for item in items:
        if item.responsavel:
            if item.responsavel not in pessoas_items:
                pessoas_items[item.responsavel] = []
            pessoas_items[item.responsavel].append(item)

    # Demandas vencendo hoje e amanhã por pessoa
    pessoas_demandas_hoje = {}
    pessoas_demandas_amanha = {}

    demandas_hoje = Demanda.objects.filter(
        prazo__date=hoje,
    ).exclude(status=StatusDemanda.CONCLUIDO).select_related('responsavel', 'empresa')

    for d in demandas_hoje:
        if d.responsavel:
            pessoas_demandas_hoje.setdefault(d.responsavel, []).append(d)

    demandas_amanha = Demanda.objects.filter(
        prazo__date=amanha,
    ).exclude(status=StatusDemanda.CONCLUIDO).select_related('responsavel', 'empresa')

    for d in demandas_amanha:
        if d.responsavel:
            pessoas_demandas_amanha.setdefault(d.responsavel, []).append(d)

    # Contas a pagar hoje (envia para gestores)
    contas_hoje = list(ContaPagarItem.objects.filter(
        data_execucao=hoje, pago=False,
    ).select_related('conta_pagar', 'conta_pagar__empresa'))

    # Todas as pessoas que precisam receber algo
    todas_pessoas = set(pessoas_items.keys()) | set(pessoas_demandas_hoje.keys()) | set(pessoas_demandas_amanha.keys())

    # Gestores recebem contas a pagar
    if contas_hoje:
        gestores = Pessoa.objects.filter(is_gestor=True, ativo=True).exclude(telefone='')
        todas_pessoas |= set(gestores)

    for pessoa in todas_pessoas:
        tarefas = pessoas_items.get(pessoa, [])
        d_hoje = pessoas_demandas_hoje.get(pessoa, [])
        d_amanha = pessoas_demandas_amanha.get(pessoa, [])
        contas = contas_hoje if pessoa.is_gestor else []

        if not tarefas and not d_hoje and not d_amanha and not contas:
            continue

        mensagem = montar_mensagem_lembrete(pessoa, tarefas, d_hoje, d_amanha, contas)
        if not mensagem:
            continue

        telefone = pessoa.telefone_formatado()
        notificacao = NotificacaoWhatsApp.objects.create(
            pessoa=pessoa,
            tipo=TipoNotificacao.LEMBRETE,
            mensagem=mensagem,
            telefone=telefone,
        )

        client = WAPIClient()
        res = client.enviar_mensagem(telefone, mensagem)

        if res['success']:
            notificacao.enviado = True
            notificacao.enviado_em = timezone.now()
            resultado['enviados'] += 1
        else:
            notificacao.erro = res.get('error', 'Erro desconhecido')
            resultado['erros'] += 1
        notificacao.save()

        # Marca tarefas como lembrete enviado
        for item in tarefas:
            item.lembrete_enviado = True
            item.save()

    return resultado


def processar_cobrancas(force=True):
    """Processa e envia cobranças de tarefas não concluídas

    Args:
        force: Se True, envia mesmo se cobrança já foi enviada antes (default para botão manual)
    """
    from checklists.models import ChecklistItem, StatusItem

    hoje = timezone.localdate()
    resultado = {'enviados': 0, 'erros': 0, 'detalhes': [], 'debug': {}}

    # Verifica se W-API está configurada
    client = WAPIClient()
    if not client.esta_configurado():
        resultado['error'] = 'W-API não configurado'
        return resultado

    # Agrupa itens não concluídos por pessoa
    pessoas_items = {}

    filtros = {
        'data_referencia': hoje,
        'status__in': [StatusItem.PENDENTE, StatusItem.EM_ANDAMENTO, StatusItem.ATRASADO],
        'template__enviar_lembrete': True,
    }

    # Se não forçar, só envia itens que não tiveram cobrança ainda
    if not force:
        filtros['cobranca_enviada'] = False

    items = ChecklistItem.objects.filter(**filtros).select_related('responsavel', 'template')

    resultado['debug']['total_itens_encontrados'] = items.count()

    for item in items:
        if item.responsavel and item.responsavel.telefone:
            if item.responsavel not in pessoas_items:
                pessoas_items[item.responsavel] = []
            pessoas_items[item.responsavel].append(item)

    resultado['debug']['pessoas_com_pendencias'] = len(pessoas_items)

    if not pessoas_items:
        resultado['debug']['motivo'] = 'Nenhuma pendência encontrada para enviar'
        return resultado

    # Envia para cada pessoa
    for pessoa, pessoa_items in pessoas_items.items():
        # Verifica se pessoa aceita lembretes
        if not pessoa.receber_lembretes:
            resultado['detalhes'].append({
                'nome': pessoa.nome,
                'status': 'skip',
                'motivo': 'Não recebe lembretes'
            })
            continue

        mensagem = montar_mensagem_cobranca(pessoa, pessoa_items)
        if not mensagem:
            resultado['detalhes'].append({
                'nome': pessoa.nome,
                'status': 'skip',
                'motivo': 'Mensagem vazia'
            })
            continue

        telefone = pessoa.telefone_formatado()

        notificacao = NotificacaoWhatsApp.objects.create(
            pessoa=pessoa,
            tipo=TipoNotificacao.COBRANCA,
            mensagem=mensagem,
            telefone=telefone
        )

        res = client.enviar_mensagem(telefone, mensagem)

        if res['success']:
            notificacao.enviado = True
            notificacao.enviado_em = timezone.now()
            resultado['enviados'] += 1
            resultado['detalhes'].append({
                'nome': pessoa.nome,
                'pendencias': len(pessoa_items),
                'status': 'ok'
            })
            # Marca itens como cobrança enviada
            for item in pessoa_items:
                item.cobranca_enviada = True
                item.save()
        else:
            notificacao.erro = res.get('error', 'Erro desconhecido')
            resultado['erros'] += 1
            resultado['detalhes'].append({
                'nome': pessoa.nome,
                'pendencias': len(pessoa_items),
                'status': 'erro',
                'error': res.get('error', 'Erro desconhecido')
            })

        notificacao.save()

    return resultado


def processar_cobrancas_externas():
    """Cobra todas as pendências agrupadas por pessoa externa (nome+telefone)"""
    from checklists.models import ChecklistItem, StatusItem, Demanda, StatusDemanda

    resultado = {'enviados': 0, 'erros': 0, 'detalhes': []}

    # Agrupar por telefone externo
    pendencias_por_telefone = {}

    tarefas = ChecklistItem.objects.filter(
        status=StatusItem.DEPENDENTE,
        telefone_dependente_externo__gt='',
    ).select_related('template', 'responsavel')

    for t in tarefas:
        tel = t.telefone_dependente_externo
        if tel not in pendencias_por_telefone:
            pendencias_por_telefone[tel] = {
                'nome': t.dependente_externo,
                'telefone': tel,
                'itens': [],
            }
        pendencias_por_telefone[tel]['itens'].append({
            'tipo': 'Tarefa',
            'titulo': t.template.titulo if t.template else 'Tarefa',
            'motivo': t.motivo_dependencia,
            'responsavel': t.responsavel.nome if t.responsavel else '',
        })

    demandas = Demanda.objects.filter(
        status=StatusDemanda.DEPENDENTE,
        telefone_dependente_externo__gt='',
    ).select_related('responsavel')

    for d in demandas:
        tel = d.telefone_dependente_externo
        if tel not in pendencias_por_telefone:
            pendencias_por_telefone[tel] = {
                'nome': d.dependente_externo,
                'telefone': tel,
                'itens': [],
            }
        pendencias_por_telefone[tel]['itens'].append({
            'tipo': 'Demanda',
            'titulo': d.titulo,
            'motivo': d.motivo_dependencia,
            'responsavel': d.responsavel.nome if d.responsavel else '',
        })

    client = WAPIClient()
    if not client.esta_configurado():
        return {'enviados': 0, 'erros': 0, 'error': 'WAPI não configurado'}

    for tel, dados in pendencias_por_telefone.items():
        nome = dados['nome']
        itens = dados['itens']
        telefone = ''.join(filter(str.isdigit, tel))
        if not telefone.startswith('55'):
            telefone = '55' + telefone

        mensagem = f"Olá *{nome}*! 👋\n\n"
        mensagem += f"Você tem *{len(itens)} pendência(s)* conosco:\n\n"

        for i, item in enumerate(itens, 1):
            mensagem += f"{i}. *{item['titulo']}*\n"
            if item['motivo']:
                mensagem += f"   📌 {item['motivo']}\n"
            if item['responsavel']:
                mensagem += f"   👤 Solicitado por: {item['responsavel']}\n"
            mensagem += "\n"

        mensagem += "Pode nos dar uma posição? 🙏\n\n"
        mensagem += "_Enviado via NeuraxoCheck_"

        res = client.enviar_mensagem(telefone, mensagem)

        NotificacaoWhatsApp.objects.create(
            pessoa=Pessoa.objects.filter(is_gestor=True).first(),
            tipo=TipoNotificacao.COBRANCA,
            mensagem=mensagem,
            telefone=telefone,
            enviado=res['success'],
            enviado_em=timezone.now() if res['success'] else None,
            erro=res.get('error', ''),
        )

        if res['success']:
            resultado['enviados'] += 1
            resultado['detalhes'].append({'nome': nome, 'pendencias': len(itens), 'status': 'ok'})
        else:
            resultado['erros'] += 1
            resultado['detalhes'].append({'nome': nome, 'pendencias': len(itens), 'status': 'erro', 'error': res.get('error')})

    return resultado


def processar_contas_pagar():
    """Envia lembrete de contas a pagar do dia para pessoas configuradas por empresa"""
    from financeiro.models import ContaPagarItem

    hoje = timezone.localdate()
    resultado = {'enviados': 0, 'erros': 0, 'detalhes': []}

    client = WAPIClient()
    if not client.esta_configurado():
        return {'enviados': 0, 'erros': 0, 'error': 'W-API não configurado'}

    # Contas a pagar hoje (não pagas)
    contas_hoje = list(ContaPagarItem.objects.filter(
        data_execucao=hoje, pago=False,
    ).select_related('conta_pagar', 'conta_pagar__empresa'))

    # Contas atrasadas
    contas_atrasadas = list(ContaPagarItem.objects.filter(
        data_execucao__lt=hoje, pago=False,
    ).select_related('conta_pagar', 'conta_pagar__empresa'))

    if not contas_hoje and not contas_atrasadas:
        return {'enviados': 0, 'erros': 0, 'detalhes': [], 'debug': {'motivo': 'Nenhuma conta a pagar pendente'}}

    # Buscar pessoas que têm empresas configuradas para lembrete financeiro
    destinatarios = Pessoa.objects.filter(
        ativo=True,
        empresas_lembrete_financeiro__isnull=False
    ).exclude(telefone='').distinct().prefetch_related('empresas_lembrete_financeiro')

    for pessoa in destinatarios:
        # Pegar as empresas que essa pessoa recebe lembrete
        empresas_pessoa = set(pessoa.empresas_lembrete_financeiro.values_list('id', flat=True))

        if not empresas_pessoa:
            continue

        # Filtrar contas apenas das empresas que a pessoa tem acesso
        contas_hoje_pessoa = [c for c in contas_hoje if c.conta_pagar.empresa_id in empresas_pessoa]
        contas_atrasadas_pessoa = [c for c in contas_atrasadas if c.conta_pagar.empresa_id in empresas_pessoa]

        if not contas_hoje_pessoa and not contas_atrasadas_pessoa:
            continue

        # Montar mensagem
        linhas = [f"💰 *Olá, {pessoa.nome.split()[0]}!*", ""]

        if contas_atrasadas_pessoa:
            total_atrasado = sum(c.valor for c in contas_atrasadas_pessoa)
            linhas.append(f"🔴 *{len(contas_atrasadas_pessoa)} conta(s) ATRASADA(S) - R$ {total_atrasado:,.2f}:*")
            for c in contas_atrasadas_pessoa:
                empresa_nome = c.conta_pagar.empresa.nome if c.conta_pagar.empresa else ''
                linhas.append(f"• [{empresa_nome}] {c.conta_pagar.descricao} - R$ {c.valor:,.2f} (venc. {c.data_vencimento.strftime('%d/%m')})")
            linhas.append("")

        if contas_hoje_pessoa:
            total_hoje = sum(c.valor for c in contas_hoje_pessoa)
            linhas.append(f"📅 *{len(contas_hoje_pessoa)} conta(s) para HOJE - R$ {total_hoje:,.2f}:*")
            for c in contas_hoje_pessoa:
                empresa_nome = c.conta_pagar.empresa.nome if c.conta_pagar.empresa else ''
                linhas.append(f"• [{empresa_nome}] {c.conta_pagar.descricao} - R$ {c.valor:,.2f}")
            linhas.append("")

        linhas.extend([
            "Acesse o sistema para pagar.",
            "",
            "*Neuraxo-Check - Mensagem Automática*"
        ])

        mensagem = "\n".join(linhas)
        telefone = pessoa.telefone_formatado()

        notificacao = NotificacaoWhatsApp.objects.create(
            pessoa=pessoa,
            tipo=TipoNotificacao.LEMBRETE,
            mensagem=mensagem,
            telefone=telefone,
        )

        res = client.enviar_mensagem(telefone, mensagem)

        if res['success']:
            notificacao.enviado = True
            notificacao.enviado_em = timezone.now()
            resultado['enviados'] += 1
            resultado['detalhes'].append({
                'nome': pessoa.nome,
                'contas_hoje': len(contas_hoje_pessoa),
                'contas_atrasadas': len(contas_atrasadas_pessoa),
                'status': 'ok'
            })
        else:
            notificacao.erro = res.get('error', 'Erro desconhecido')
            resultado['erros'] += 1
            resultado['detalhes'].append({
                'nome': pessoa.nome,
                'status': 'erro',
                'error': res.get('error')
            })
        notificacao.save()

    return resultado


def processar_resumo_dependencias():
    """Envia para cada pessoa um resumo de tudo que ela está aguardando (internas + externas)"""
    from checklists.models import ChecklistItem, StatusItem, Demanda, StatusDemanda

    resultado = {'enviados': 0, 'erros': 0}
    client = WAPIClient()
    if not client.esta_configurado():
        return {'enviados': 0, 'erros': 0, 'error': 'WAPI não configurado'}

    # Para cada pessoa ativa com telefone
    pessoas = Pessoa.objects.filter(ativo=True).exclude(telefone='')

    for pessoa in pessoas:
        pendencias = []

        # Tarefas onde EU marquei dependência de alguém (interno)
        tarefas_dep_interna = ChecklistItem.objects.filter(
            responsavel=pessoa,
            status=StatusItem.DEPENDENTE,
            dependente_de__isnull=False,
        ).select_related('template', 'dependente_de')

        for t in tarefas_dep_interna:
            pendencias.append({
                'tipo': 'Tarefa',
                'titulo': t.template.titulo if t.template else 'Tarefa',
                'aguardando': t.dependente_de.nome,
                'motivo': t.motivo_dependencia,
                'externo': False,
            })

        # Tarefas onde EU marquei dependência de alguém (externo)
        tarefas_dep_externa = ChecklistItem.objects.filter(
            responsavel=pessoa,
            status=StatusItem.DEPENDENTE,
            dependente_externo__gt='',
        ).select_related('template')

        for t in tarefas_dep_externa:
            pendencias.append({
                'tipo': 'Tarefa',
                'titulo': t.template.titulo if t.template else 'Tarefa',
                'aguardando': t.dependente_externo,
                'motivo': t.motivo_dependencia,
                'externo': True,
            })

        # Demandas onde EU marquei dependência (interna)
        demandas_dep_interna = Demanda.objects.filter(
            responsavel=pessoa,
            status=StatusDemanda.DEPENDENTE,
            dependente_de__isnull=False,
        ).select_related('dependente_de')

        for d in demandas_dep_interna:
            pendencias.append({
                'tipo': 'Demanda',
                'titulo': d.titulo,
                'aguardando': d.dependente_de.nome,
                'motivo': d.motivo_dependencia,
                'externo': False,
            })

        # Demandas onde EU marquei dependência (externa)
        demandas_dep_externa = Demanda.objects.filter(
            responsavel=pessoa,
            status=StatusDemanda.DEPENDENTE,
            dependente_externo__gt='',
        )

        for d in demandas_dep_externa:
            pendencias.append({
                'tipo': 'Demanda',
                'titulo': d.titulo,
                'aguardando': d.dependente_externo,
                'motivo': d.motivo_dependencia,
                'externo': True,
            })

        if not pendencias:
            continue

        # Montar mensagem
        nome = pessoa.nome.split()[0]
        mensagem = f"📋 *{nome}, suas pendências com outras pessoas:*\n\n"
        mensagem += f"Você tem *{len(pendencias)} item(ns)* aguardando retorno:\n\n"

        for i, p in enumerate(pendencias, 1):
            ext = " 🔸" if p['externo'] else ""
            mensagem += f"{i}. *{p['titulo']}*\n"
            mensagem += f"   ⏳ Aguardando: *{p['aguardando']}*{ext}\n"
            if p['motivo']:
                mensagem += f"   📌 {p['motivo']}\n"
            mensagem += "\n"

        mensagem += "Acesse o NeuraxoCheck para mais detalhes.\n\n"
        mensagem += "*Neuraxo-Check - Mensagem Automática*"

        telefone = pessoa.telefone_formatado()
        res = client.enviar_mensagem(telefone, mensagem)

        NotificacaoWhatsApp.objects.create(
            pessoa=pessoa,
            tipo=TipoNotificacao.LEMBRETE,
            mensagem=mensagem,
            telefone=telefone,
            enviado=res['success'],
            enviado_em=timezone.now() if res['success'] else None,
            erro=res.get('error', ''),
        )

        if res['success']:
            resultado['enviados'] += 1
        else:
            resultado['erros'] += 1

    return resultado
