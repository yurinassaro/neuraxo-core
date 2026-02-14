"""
Comando para fechar o dia e calcular aproveitamento.
Deve ser executado às 23:59 via cron/celery.

Uso:
    python manage.py fechar_dia
    python manage.py fechar_dia --data=2026-01-27
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection
from datetime import datetime, timedelta
from checklists.models import (
    ChecklistItem, ChecklistTemplate, StatusItem,
    AproveitamentoDiario, TarefaNaoConcluida
)
from core.models import Pessoa
from tenants.models import Client


class Command(BaseCommand):
    help = 'Fecha o dia, calcula aproveitamento e prepara tarefas não concluídas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data',
            type=str,
            help='Data específica para fechar (formato: YYYY-MM-DD). Se não informada, usa hoje.',
        )

    def handle(self, *args, **options):
        if options['data']:
            data = datetime.strptime(options['data'], '%Y-%m-%d').date()
        else:
            data = timezone.localdate()

        self.stdout.write(f'Fechando dia {data}...\n')

        # Iterar por todos os tenants (exceto public)
        tenants = Client.objects.exclude(schema_name='public')

        for tenant in tenants:
            self.stdout.write(f'\n[{tenant.nome}] Schema: {tenant.schema_name}')

            # Mudar para o schema do tenant
            connection.set_tenant(tenant)

            total_pessoas = 0
            total_tarefas_fechadas = 0

            # Buscar todas as pessoas ativas
            pessoas = Pessoa.objects.filter(ativo=True)

            for pessoa in pessoas:
                # Buscar tarefas do dia desta pessoa
                items = ChecklistItem.objects.filter(
                    responsavel=pessoa,
                    data_referencia=data,
                    dia_fechado=False
                )

                if not items.exists():
                    continue

                total_pessoas += 1

                # Calcular aproveitamento
                aproveitamento = AproveitamentoDiario.calcular_para_pessoa(pessoa, data)
                aproveitamento.fechado_em = timezone.now()
                aproveitamento.save()

                # Marcar tarefas não concluídas
                for item in items:
                    item.dia_fechado = True

                    # Se não concluiu e não tem justificativa, registrar como pendente de justificativa
                    if item.status != StatusItem.CONCLUIDO:
                        # Criar registro de tarefa não concluída
                        TarefaNaoConcluida.objects.get_or_create(
                            checklist_item=item,
                            aproveitamento=aproveitamento,
                            defaults={
                                'justificativa': item.justificativa or 'Pendente de justificativa'
                            }
                        )

                    item.save()
                    total_tarefas_fechadas += 1

                self.stdout.write(
                    f'  {pessoa.nome}: {aproveitamento.tarefas_concluidas}/{aproveitamento.total_tarefas} '
                    f'({aproveitamento.percentual:.0f}%)'
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f'  [{tenant.nome}] {total_pessoas} pessoa(s), {total_tarefas_fechadas} tarefa(s) processada(s).'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f'\nDia {data} fechado para todos os tenants!')
        )
