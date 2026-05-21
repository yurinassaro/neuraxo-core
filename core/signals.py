from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='core.Empresa')
def vincular_empresa_ao_admin(sender, instance, created, **kwargs):
    """Ao criar uma nova Empresa, vincula automaticamente ao admin principal (user.is_superuser)."""
    if not created:
        return

    from core.models import Pessoa
    admin = Pessoa.objects.filter(user__is_superuser=True, ativo=True).first()
    if admin:
        admin.empresas.add(instance)


@receiver(post_save, sender='core.Cliente')
def criar_pastas_padrao_cliente(sender, instance, created, **kwargs):
    """Ao criar um cliente, cria pastas padrão baseadas no template da empresa"""
    if not created or not instance.empresa:
        return
    from core.models import PastaTemplateEmpresa, PastaCliente

    templates = PastaTemplateEmpresa.objects.filter(empresa=instance.empresa)
    if templates.exists():
        for t in templates:
            PastaCliente.objects.get_or_create(
                cliente=instance, nome=t.nome,
                defaults={'ordem': t.ordem}
            )
    else:
        # Pastas padrão genéricas
        for i, nome in enumerate(['Materiais', 'Criativos', 'Documentos']):
            PastaCliente.objects.get_or_create(
                cliente=instance, nome=nome,
                defaults={'ordem': i}
            )


@receiver(post_save, sender='core.Cliente')
def gerar_conta_receber_cliente(sender, instance, created, **kwargs):
    """Ao criar/atualizar cliente com contrato recorrente, gera conta a receber"""
    if not instance.valor_mensal or not instance.empresa:
        return
    if instance.tipo_contrato not in ('mensal', 'quinzenal'):
        return
    if instance.status_contrato in ('cancelado',):
        return

    try:
        from financeiro.models import ContaReceber, ContaReceberItem
        from django.utils import timezone

        # Verificar se já tem conta a receber ativa
        conta_existente = ContaReceber.objects.filter(
            empresa=instance.empresa,
            cliente_empresa=instance,
            ativo=True,
        ).first()

        if conta_existente:
            if conta_existente.valor != instance.valor_mensal:
                conta_existente.valor = instance.valor_mensal
                conta_existente.save(update_fields=['valor'])
            return

        recorrencia = 'mensal' if instance.tipo_contrato == 'mensal' else 'quinzenal'
        dia = instance.dia_vencimento or 10

        conta = ContaReceber.objects.create(
            empresa=instance.empresa,
            cliente_empresa=instance,
            descricao=f'Fee {instance.get_tipo_contrato_display()} - {instance.nome}',
            valor=instance.valor_mensal,
            recorrencia=recorrencia,
            dia_vencimento=dia,
            data_vencimento=instance.data_inicio_contrato or timezone.localdate(),
            ativo=True,
        )

        # Gerar primeiro item
        hoje = timezone.localdate()
        ContaReceberItem.objects.create(
            conta_receber=conta,
            mes=hoje.month,
            ano=hoje.year,
            valor=instance.valor_mensal,
            data_vencimento=hoje.replace(day=min(dia, 28)),
        )
    except Exception as e:
        print(f'[Signal] Erro ao gerar conta a receber: {e}')


@receiver(post_save, sender='checklists.ChecklistTemplate')
def gerar_tarefa_ao_criar_rotina(sender, instance, created, **kwargs):
    """Ao criar rotina nova, gera tarefa do dia se ainda não existe"""
    if not created or not instance.ativo:
        return
    try:
        from checklists.models import ChecklistItem, SubTarefa
        from django.utils import timezone
        from datetime import timedelta

        hoje = timezone.localdate()

        # Verificar se é dia ativo
        dia_semana = str(hoje.weekday())
        if instance.dias_semana_ativos and dia_semana not in instance.dias_semana_ativos.split(','):
            return

        # Pegar responsáveis
        responsaveis = []
        if instance.responsavel:
            responsaveis = [instance.responsavel]
        elif instance.responsavel_todos:
            from core.models import Pessoa
            responsaveis = list(Pessoa.objects.filter(empresas=instance.empresa, ativo=True))
        elif instance.cargo_responsavel:
            from core.models import Pessoa
            responsaveis = list(Pessoa.objects.filter(cargo=instance.cargo_responsavel, ativo=True))

        for resp in responsaveis:
            # Verificar se já existe
            if ChecklistItem.objects.filter(template=instance, responsavel=resp, data_referencia=hoje).exists():
                continue

            item = ChecklistItem.objects.create(
                template=instance,
                responsavel=resp,
                data_referencia=hoje,
                data_limite=timezone.make_aware(
                    timezone.datetime.combine(hoje, timezone.datetime.max.time())
                ),
            )
            # Copiar subtarefas
            for st in instance.subtarefas_template.all():
                SubTarefa.objects.create(
                    checklist_item=item, titulo=st.titulo, ordem=st.ordem,
                )
    except Exception as e:
        print(f'[Signal] Erro ao gerar tarefa: {e}')


@receiver(post_save, sender='checklists.Demanda')
def notificar_nova_demanda(sender, instance, created, **kwargs):
    """Notifica o responsável quando uma demanda é criada"""
    from core.models import NotificacaoInApp

    if not created or not instance.responsavel:
        return

    # Não notificar o próprio solicitante
    if instance.solicitante and instance.responsavel_id == instance.solicitante_id:
        return

    try:
        NotificacaoInApp.criar(
            destinatario=instance.responsavel,
            tipo='demanda',
            titulo=f'Nova demanda: {instance.titulo}',
            mensagem=f'{instance.empresa.nome} | Prazo: {instance.prazo.strftime("%d/%m/%Y") if instance.prazo else "sem prazo"}',
            url=f'/demanda/{instance.id}/',
        )
    except Exception:
        pass


@receiver(post_save, sender='checklists.ComentarioDemanda')
def notificar_comentario(sender, instance, created, **kwargs):
    """Notifica quando alguém comenta numa demanda"""
    from core.models import NotificacaoInApp

    if not created:
        return

    demanda = instance.demanda
    autor = instance.autor

    try:
        # Notificar responsável
        if demanda.responsavel and demanda.responsavel != autor:
            NotificacaoInApp.criar(
                destinatario=demanda.responsavel,
                tipo='comentario',
                titulo=f'Comentário em: {demanda.titulo}',
                mensagem=f'{autor.nome} comentou',
                url=f'/demanda/{demanda.id}/',
            )

        # Notificar criador
        if demanda.criado_por and demanda.criado_por != autor and demanda.criado_por != demanda.responsavel:
            NotificacaoInApp.criar(
                destinatario=demanda.criado_por,
                tipo='comentario',
                titulo=f'{autor.nome} comentou em: {demanda.titulo}',
                mensagem=f'{demanda.empresa.nome}',
                url=f'/demanda/{demanda.id}/',
            )
    except Exception:
        pass
