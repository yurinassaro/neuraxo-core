"""
Envia cobranças para pessoas externas com pendências.
Uso: python manage.py cobrar_externos [--force]

Por padrão, envia apenas 1x por semana (segundas-feiras).
Use --force para enviar independente do dia.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Envia cobranças via WhatsApp para pessoas externas com pendências'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Enviar independente do dia da semana',
        )

    def handle(self, *args, **options):
        hoje = timezone.localdate()

        # Por padrão envia apenas nas segundas (weekday 0) e quintas (weekday 3)
        if not options['force'] and hoje.weekday() not in [0, 3]:
            self.stdout.write(f'Hoje é {hoje.strftime("%A")} - cobranças externas são enviadas seg/qui. Use --force para forçar.')
            return

        from notifications.wapi import processar_cobrancas_externas

        self.stdout.write('Processando cobranças externas...')
        resultado = processar_cobrancas_externas()

        if 'error' in resultado:
            self.stdout.write(self.style.ERROR(f'Erro: {resultado["error"]}'))
            return

        self.stdout.write(self.style.SUCCESS(
            f'Enviados: {resultado["enviados"]} | Erros: {resultado["erros"]}'
        ))

        for d in resultado.get('detalhes', []):
            status = '✓' if d['status'] == 'ok' else '✗'
            self.stdout.write(f'  {status} {d["nome"]}: {d["pendencias"]} pendência(s)')
