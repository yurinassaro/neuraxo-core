"""
Comando para gerar checklists do dia
Uso: python manage.py gerar_checklists
"""
from django.core.management.base import BaseCommand
from checklists.services import gerar_checklists_do_dia, atualizar_status_atrasados


class Command(BaseCommand):
    help = 'Gera os checklists do dia baseado nos templates ativos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--atualizar-atrasados',
            action='store_true',
            help='Também atualiza status de itens atrasados'
        )

    def handle(self, *args, **options):
        self.stdout.write('Gerando checklists do dia...')

        resultado = gerar_checklists_do_dia()

        self.stdout.write(f"Data: {resultado['data']}")
        self.stdout.write(self.style.SUCCESS(f"Gerados: {resultado['gerados']}"))
        self.stdout.write(f"Ignorados (já existiam): {resultado['ignorados']}")

        if resultado['erros']:
            self.stdout.write(self.style.WARNING('Erros:'))
            for erro in resultado['erros']:
                self.stdout.write(f"  - {erro}")

        if options['atualizar_atrasados']:
            count = atualizar_status_atrasados()
            self.stdout.write(f"Itens marcados como atrasados: {count}")

        self.stdout.write(self.style.SUCCESS('Concluído!'))
