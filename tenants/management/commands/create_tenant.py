from django.core.management.base import BaseCommand
from tenants.models import Client, Domain


class Command(BaseCommand):
    help = 'Cria um novo tenant com domínio'

    def add_arguments(self, parser):
        parser.add_argument('nome', type=str, help='Nome do tenant (ex: Grupo Yuri)')
        parser.add_argument('schema', type=str, help='Nome do schema (ex: grupo_yuri)')
        parser.add_argument('subdomain', type=str, help='Subdomínio (ex: grupoyuri)')
        parser.add_argument('--domain-base', type=str, default='core.neuraxo.com.br',
                            help='Domínio base (default: core.neuraxo.com.br)')

    def handle(self, *args, **options):
        schema = options['schema']
        nome = options['nome']
        subdomain = options['subdomain']
        domain_base = options['domain_base']

        if Client.objects.filter(schema_name=schema).exists():
            self.stdout.write(self.style.WARNING(f'Tenant "{schema}" já existe.'))
            return

        tenant = Client(
            schema_name=schema,
            nome=nome,
        )
        tenant.save()  # auto_create_schema=True vai criar o schema

        full_domain = f'{subdomain}.{domain_base}'
        Domain.objects.create(
            domain=full_domain,
            tenant=tenant,
            is_primary=True,
        )

        self.stdout.write(self.style.SUCCESS(
            f'Tenant "{nome}" criado!\n'
            f'  Schema: {schema}\n'
            f'  Domínio: {full_domain}'
        ))
