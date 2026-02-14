from django.core.management.base import BaseCommand
from tenants.models import Client, Domain


class Command(BaseCommand):
    help = 'Cria o tenant público (schema public) se não existir'

    def handle(self, *args, **options):
        if Client.objects.filter(schema_name='public').exists():
            self.stdout.write('Tenant público já existe.')
            return

        tenant = Client(
            schema_name='public',
            nome='NeuraxoCheck Admin',
        )
        tenant.auto_create_schema = False  # schema public já existe
        tenant.save()

        # Domínio principal (sem subdomain)
        Domain.objects.create(
            domain='core.neuraxo.com.br',
            tenant=tenant,
            is_primary=True,
        )
        # Domínio local para dev
        Domain.objects.create(
            domain='localhost',
            tenant=tenant,
            is_primary=False,
        )

        self.stdout.write(self.style.SUCCESS('Tenant público criado com sucesso!'))
