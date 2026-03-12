"""
Comando para criar/atualizar acesso compartilhado entre tenants.

Uso:
    python manage.py compartilhar_acesso admin.grupo_yuri grupo_ronaldo --empresa Plantec --gestor
    python manage.py compartilhar_acesso admin.grupo_yuri grupo_ronaldo --empresa Plantec --empresa "Outra Empresa"
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django_tenants.utils import schema_context
from tenants.models import Client, AcessoCompartilhado


class Command(BaseCommand):
    help = 'Cria ou atualiza acesso compartilhado para um usuário em outro tenant'

    def add_arguments(self, parser):
        parser.add_argument('username', help='Username do usuário (ex: admin.grupo_yuri)')
        parser.add_argument('tenant_schema', help='Schema do tenant destino (ex: grupo_ronaldo)')
        parser.add_argument('--empresa', action='append', dest='empresas', help='Nome da empresa permitida (pode repetir)')
        parser.add_argument('--gestor', action='store_true', help='Dar permissão de gestor')
        parser.add_argument('--remover', action='store_true', help='Remover acesso compartilhado')

    def handle(self, *args, **options):
        username = options['username']
        tenant_schema = options['tenant_schema']
        empresas_nomes = options.get('empresas') or []
        is_gestor = options['gestor']
        remover = options['remover']

        # Buscar usuário
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Usuário "{username}" não encontrado.'))
            return

        # Buscar tenant destino
        try:
            tenant = Client.objects.get(schema_name=tenant_schema)
        except Client.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Tenant "{tenant_schema}" não encontrado.'))
            self.stdout.write('Tenants disponíveis:')
            for t in Client.objects.exclude(schema_name='public'):
                self.stdout.write(f'  - {t.schema_name} ({t.nome})')
            return

        # Remover acesso
        if remover:
            deleted, _ = AcessoCompartilhado.objects.filter(user=user, tenant_destino=tenant).delete()
            if deleted:
                self.stdout.write(self.style.SUCCESS(f'Acesso removido: {username} → {tenant.nome}'))
            else:
                self.stdout.write(self.style.WARNING('Nenhum acesso encontrado para remover.'))
            return

        # Buscar IDs das empresas no tenant destino
        empresas_ids = []
        with schema_context(tenant_schema):
            from core.models import Empresa
            if empresas_nomes:
                for nome in empresas_nomes:
                    try:
                        empresa = Empresa.objects.get(nome__iexact=nome, ativo=True)
                        empresas_ids.append(empresa.id)
                        self.stdout.write(f'  Empresa encontrada: {empresa.nome} (ID: {empresa.id})')
                    except Empresa.DoesNotExist:
                        self.stderr.write(self.style.WARNING(f'  Empresa "{nome}" não encontrada no tenant {tenant.nome}.'))
                        self.stdout.write('  Empresas disponíveis:')
                        for e in Empresa.objects.filter(ativo=True):
                            self.stdout.write(f'    - {e.nome} (ID: {e.id})')
                        return
            else:
                self.stdout.write('Empresas disponíveis no tenant:')
                for e in Empresa.objects.filter(ativo=True):
                    self.stdout.write(f'  - {e.nome} (ID: {e.id})')
                self.stderr.write(self.style.WARNING('Use --empresa "Nome" para selecionar.'))
                return

        # Criar ou atualizar acesso
        acesso, created = AcessoCompartilhado.objects.update_or_create(
            user=user,
            tenant_destino=tenant,
            defaults={
                'is_gestor': is_gestor,
                'empresas_ids': empresas_ids,
                'ativo': True,
            }
        )

        acao = 'Criado' if created else 'Atualizado'
        papel = 'Gestor' if is_gestor else 'Funcionário'
        self.stdout.write(self.style.SUCCESS(
            f'{acao}: {username} → {tenant.nome} ({papel}) | Empresas: {empresas_nomes}'
        ))
