"""
Migra dados existentes do schema public para um novo tenant.
Uso: python manage.py migrate_to_tenant "Grupo Yuri" grupo_yuri grupoyuri

Este comando:
1. Cria o tenant (schema) se não existir
2. Copia dados das tabelas tenant-only do public para o novo schema
3. Mantém os IDs originais

IMPORTANTE: Rodar APENAS UMA VEZ na migração inicial.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from tenants.models import Client, Domain


# Tabelas que pertencem a TENANT_APPS (serão copiadas do public para o schema)
TENANT_TABLES = [
    # auth/contenttypes FIRST (other tables have FK to these)
    'django_content_type',
    'auth_permission',
    'auth_group',
    'auth_group_permissions',
    'auth_user',
    'auth_user_groups',
    'auth_user_user_permissions',
    # core (depends on auth_user)
    'core_empresa',
    'core_cargo',
    'core_pessoa',
    'core_pessoa_empresas',
    'core_pessoaexterna',
    # checklists (depends on core)
    'checklists_checklisttemplate',
    'checklists_subtarefatemplate',
    'checklists_checklistitem',
    'checklists_subtarefa',
    'checklists_projeto',
    'checklists_projeto_participantes',
    'checklists_demanda',
    'checklists_subtarefademanda',
    'checklists_anexodemanda',
    'checklists_comentariodemanda',
    'checklists_aproveitamentodiario',
    'checklists_tarefanaoconcluida',
    # notifications
    'notifications_agendamentonotificacao',
    'notifications_lognotificacao',
    # financeiro
    'financeiro_categoriafinanceira',
    'financeiro_contapagar',
    'financeiro_contapagarrecorrente',
    'financeiro_venda',
    # sessions
    'django_session',
]


class Command(BaseCommand):
    help = 'Migra dados do schema public para um novo tenant'

    def add_arguments(self, parser):
        parser.add_argument('nome', type=str)
        parser.add_argument('schema', type=str)
        parser.add_argument('subdomain', type=str)
        parser.add_argument('--domain-base', default='core.neuraxo.com.br')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        nome = options['nome']
        schema = options['schema']
        subdomain = options['subdomain']
        domain_base = options['domain_base']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN ==='))

        # 1. Criar tenant
        tenant, created = Client.objects.get_or_create(
            schema_name=schema,
            defaults={'nome': nome}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Tenant "{nome}" criado (schema: {schema})'))
        else:
            self.stdout.write(f'Tenant "{nome}" já existe.')

        # Criar domínio
        full_domain = f'{subdomain}.{domain_base}'
        Domain.objects.get_or_create(
            domain=full_domain,
            tenant=tenant,
            defaults={'is_primary': True}
        )
        # Domínio localhost para dev
        Domain.objects.get_or_create(
            domain=f'{subdomain}.localhost',
            tenant=tenant,
            defaults={'is_primary': False}
        )

        if dry_run:
            self.stdout.write('Dry run: não copiando dados.')
            return

        # 2. Copiar dados do public para o novo schema
        with connection.cursor() as cursor:
            for table in TENANT_TABLES:
                try:
                    # Verificar se tabela existe no public
                    cursor.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s)", [table])
                    exists = cursor.fetchone()[0]
                    if not exists:
                        self.stdout.write(f'  SKIP {table} (não existe no public)')
                        continue

                    # Verificar se tabela existe no schema destino
                    cursor.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = %s)", [schema, table])
                    dest_exists = cursor.fetchone()[0]
                    if not dest_exists:
                        self.stdout.write(f'  SKIP {table} (não existe no schema {schema})')
                        continue

                    # Contar registros no public
                    cursor.execute(f'SELECT COUNT(*) FROM public."{table}"')
                    count = cursor.fetchone()[0]
                    if count == 0:
                        self.stdout.write(f'  SKIP {table} (vazia)')
                        continue

                    # Copiar dados
                    cursor.execute(f'INSERT INTO "{schema}"."{table}" SELECT * FROM public."{table}" ON CONFLICT DO NOTHING')
                    self.stdout.write(self.style.SUCCESS(f'  OK {table}: {count} registros copiados'))

                    # Atualizar sequences (auto-increment)
                    cursor.execute(f"""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = %s AND column_name = 'id'
                    """, [schema, table])
                    if cursor.fetchone():
                        cursor.execute(f"""
                            SELECT setval(pg_get_serial_sequence('"{schema}"."{table}"', 'id'),
                                   COALESCE((SELECT MAX(id) FROM "{schema}"."{table}"), 1))
                        """)

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ERRO {table}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\nMigração concluída! Acesse: {full_domain}'))
