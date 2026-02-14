"""
Comando para gerar tarefas do dia baseado nos templates recorrentes.
Deve ser executado às 00:00 via cron/celery.

Uso:
    python manage.py gerar_tarefas_dia
    python manage.py gerar_tarefas_dia --data=2026-01-28
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from checklists.models import ChecklistTemplate, ChecklistItem, Recorrencia, DiaSemana, SubTarefa
from core.models import Pessoa


class Command(BaseCommand):
    help = 'Gera as tarefas do dia baseado nos templates recorrentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data',
            type=str,
            help='Data específica para gerar (formato: YYYY-MM-DD). Se não informada, usa hoje.',
        )

    def handle(self, *args, **options):
        if options['data']:
            data = datetime.strptime(options['data'], '%Y-%m-%d').date()
        else:
            data = timezone.localdate()

        self.stdout.write(f'Gerando tarefas para {data}...')

        # Dia da semana (0=segunda, 6=domingo)
        dia_semana = data.weekday()
        dia_mes = data.day

        # Buscar templates ativos
        templates = ChecklistTemplate.objects.filter(ativo=True)
        total_criadas = 0

        for template in templates:
            # Verificar se deve gerar para este dia
            if not self.deve_gerar(template, data, dia_semana, dia_mes):
                continue

            # Determinar responsáveis
            responsaveis = self.get_responsaveis(template)

            for responsavel in responsaveis:
                # Verificar se já existe
                exists = ChecklistItem.objects.filter(
                    template=template,
                    responsavel=responsavel,
                    data_referencia=data
                ).exists()

                if exists:
                    continue

                # Criar item
                # Data limite: fim do dia por padrão
                data_limite = timezone.make_aware(
                    datetime.combine(data, datetime.max.time().replace(microsecond=0))
                )

                item = ChecklistItem.objects.create(
                    template=template,
                    responsavel=responsavel,
                    data_referencia=data,
                    data_limite=data_limite,
                    ordem=template.ordem_execucao,
                )

                # Copiar subtarefas do template
                for st in template.subtarefas_template.all():
                    SubTarefa.objects.create(
                        checklist_item=item,
                        titulo=st.titulo,
                        ordem=st.ordem,
                    )

                total_criadas += 1
                self.stdout.write(f'  Criada: {template.titulo} -> {responsavel.nome}')

        self.stdout.write(
            self.style.SUCCESS(f'\n{total_criadas} tarefa(s) criada(s) para {data}.')
        )

    def deve_gerar(self, template, data, dia_semana, dia_mes):
        """Verifica se o template deve gerar tarefa para esta data"""
        recorrencia = template.recorrencia

        if recorrencia == Recorrencia.DIARIA:
            return True

        elif recorrencia == Recorrencia.SEMANAL:
            # Verificar se é o dia da semana configurado
            return template.dia_semana == dia_semana

        elif recorrencia == Recorrencia.QUINZENAL:
            # A cada 15 dias a partir do dia configurado
            if template.dia_mes:
                return dia_mes == template.dia_mes or dia_mes == (template.dia_mes + 15) % 31 or dia_mes == template.dia_mes + 15

        elif recorrencia == Recorrencia.MENSAL:
            # Verificar se é o dia do mês configurado
            return template.dia_mes == dia_mes

        elif recorrencia == Recorrencia.TRIMESTRAL:
            # A cada 3 meses no dia configurado
            if template.dia_mes == dia_mes:
                mes = data.month
                return mes in [1, 4, 7, 10]  # Meses trimestrais

        elif recorrencia == Recorrencia.SEMESTRAL:
            # A cada 6 meses no dia configurado
            if template.dia_mes == dia_mes:
                mes = data.month
                return mes in [1, 7]  # Meses semestrais

        elif recorrencia == Recorrencia.ANUAL:
            # Uma vez por ano no dia e mês configurado
            return template.dia_mes == dia_mes and data.month == 1  # Janeiro

        return False

    def get_responsaveis(self, template):
        """Retorna lista de pessoas responsáveis pelo template"""
        if template.responsavel:
            # Responsável específico
            return [template.responsavel]

        elif template.cargo_responsavel:
            # Todos do cargo
            return list(template.cargo_responsavel.pessoas.filter(ativo=True))

        elif template.empresa:
            # Todos da empresa
            return list(template.empresa.pessoas.filter(ativo=True))

        return []
