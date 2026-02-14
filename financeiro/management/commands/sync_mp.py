from datetime import date, timedelta

from django.core.management.base import BaseCommand

from financeiro.models import ConfigMercadoPago
from financeiro.services import sync_mercadopago


class Command(BaseCommand):
    help = 'Sincroniza pagamentos do Mercado Pago para todas as empresas ativas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=1,
            help='Quantidade de dias para trás (padrão: 1)',
        )
        parser.add_argument(
            '--empresa', type=int, default=None,
            help='ID da empresa específica (padrão: todas ativas)',
        )

    def handle(self, *args, **options):
        days = options['days']
        empresa_id = options['empresa']
        data_fim = date.today()
        data_inicio = data_fim - timedelta(days=days)

        configs = ConfigMercadoPago.objects.filter(ativo=True).select_related('empresa')
        if empresa_id:
            configs = configs.filter(empresa_id=empresa_id)

        if not configs.exists():
            self.stdout.write(self.style.WARNING('Nenhuma configuração MP ativa encontrada.'))
            return

        for config in configs:
            self.stdout.write(f'Sincronizando {config.empresa.nome} ({data_inicio} a {data_fim})...')
            try:
                stats = sync_mercadopago(config, data_inicio, data_fim)
                self.stdout.write(self.style.SUCCESS(
                    f'  {stats["criados"]} vendas, {stats["taxas"]} taxas, '
                    f'{stats["estornos"]} estornos, {stats["ignorados"]} ignorados.'
                ))
                if stats['erros']:
                    for err in stats['erros']:
                        self.stdout.write(self.style.WARNING(f'  Aviso: {err}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Erro: {e}'))
