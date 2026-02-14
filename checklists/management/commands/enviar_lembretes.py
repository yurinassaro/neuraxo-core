"""
Comando para enviar lembretes e cobranças via WhatsApp
Uso: python manage.py enviar_lembretes [--tipo lembrete|cobranca]
"""
from django.core.management.base import BaseCommand
from notifications.wapi import processar_lembretes_diarios, processar_cobrancas, WAPIClient


class Command(BaseCommand):
    help = 'Envia lembretes e cobranças via WhatsApp'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            type=str,
            choices=['lembrete', 'cobranca', 'ambos'],
            default='ambos',
            help='Tipo de notificação a enviar'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula envio sem realmente enviar'
        )

    def handle(self, *args, **options):
        client = WAPIClient()

        if not client.esta_configurado():
            self.stdout.write(self.style.WARNING(
                'WAPI não configurado. Configure WAPI_URL, WAPI_TOKEN e WAPI_INSTANCE no .env'
            ))
            if not options['dry_run']:
                return

        tipo = options['tipo']

        if tipo in ['lembrete', 'ambos']:
            self.stdout.write('Processando lembretes...')
            if options['dry_run']:
                self.stdout.write(self.style.WARNING('(DRY RUN - não enviando)'))
            resultado = processar_lembretes_diarios()
            self.stdout.write(self.style.SUCCESS(f"Lembretes enviados: {resultado['enviados']}"))
            if resultado['erros']:
                self.stdout.write(self.style.ERROR(f"Erros: {resultado['erros']}"))

        if tipo in ['cobranca', 'ambos']:
            self.stdout.write('Processando cobranças...')
            if options['dry_run']:
                self.stdout.write(self.style.WARNING('(DRY RUN - não enviando)'))
            resultado = processar_cobrancas()
            self.stdout.write(self.style.SUCCESS(f"Cobranças enviadas: {resultado['enviados']}"))
            if resultado['erros']:
                self.stdout.write(self.style.ERROR(f"Erros: {resultado['erros']}"))

        self.stdout.write(self.style.SUCCESS('Concluído!'))
