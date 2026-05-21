"""
Migração: mover auth_user de cada tenant para o schema public.

Uso:
    python manage.py migrate_auth_to_public --dry-run   # apenas mostra o que faria
    python manage.py migrate_auth_to_public             # executa a migração
"""

from django.core.management.base import BaseCommand
from django.db import connection
from tenants.models import Client


class Command(BaseCommand):
    help = 'Migra auth_user de tenant schemas para public (schema único)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Apenas mostra o que faria')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        cursor = connection.cursor()

        tenant_schemas = list(
            Client.objects.exclude(schema_name='public')
            .values_list('schema_name', flat=True)
        )

        self.stdout.write(f"\nSchemas dos tenants: {tenant_schemas}")
        self.stdout.write(f"Modo: {'DRY RUN' if dry_run else 'EXECUÇÃO REAL'}\n")

        # ============================================
        # STEP 1: Merge users para public
        # ============================================
        self.stdout.write(self.style.MIGRATE_HEADING("STEP 1: Merge users para public.auth_user"))

        mapping = {}

        for schema in tenant_schemas:
            self.stdout.write(f"\n  Schema: {schema}")
            mapping[schema] = {}

            cursor.execute(f"""
                SELECT id, username, email, password, first_name, last_name,
                       is_superuser, is_staff, is_active, date_joined, last_login
                FROM {schema}.auth_user ORDER BY id
            """)
            tenant_users = cursor.fetchall()

            for row in tenant_users:
                (old_id, username, email, password, first_name, last_name,
                 is_superuser, is_staff, is_active, date_joined, last_login) = row

                cursor.execute(
                    "SELECT id FROM public.auth_user WHERE username = %s",
                    [username]
                )
                existing = cursor.fetchone()

                if existing:
                    new_id = existing[0]
                    mapping[schema][old_id] = new_id
                    self.stdout.write(f"    {username} (id={old_id}) -> ja existe no public (id={new_id})")
                else:
                    if not dry_run:
                        cursor.execute("""
                            INSERT INTO public.auth_user
                            (username, email, password, first_name, last_name,
                             is_superuser, is_staff, is_active, date_joined, last_login)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, [username, email, password, first_name, last_name,
                              is_superuser, is_staff, is_active, date_joined, last_login])
                        new_id = cursor.fetchone()[0]
                    else:
                        new_id = "NEW"
                    mapping[schema][old_id] = new_id
                    self.stdout.write(self.style.SUCCESS(
                        f"    {username} (id={old_id}) -> CRIAR no public (id={new_id})"
                    ))

        self.stdout.write(f"\n  Mapping: {mapping}")

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN - nada foi alterado."))
            return

        # ============================================
        # STEP 2: Atualizar core_pessoa.user_id
        # ============================================
        self.stdout.write(self.style.MIGRATE_HEADING("\nSTEP 2: Atualizar core_pessoa.user_id"))

        for schema in tenant_schemas:
            self.stdout.write(f"\n  Schema: {schema}")

            # Dropar FK constraint local
            cursor.execute(f"""
                ALTER TABLE {schema}.core_pessoa
                DROP CONSTRAINT IF EXISTS core_pessoa_user_id_b25225b8_fk_auth_user_id
            """)
            self.stdout.write(f"    FK constraint antigo removido")

            # Atualizar user_ids com CASE para evitar colisao de IDs
            changes = {old: new for old, new in mapping[schema].items() if old != new}
            if changes:
                case_clauses = " ".join(
                    f"WHEN {old} THEN {new}" for old, new in changes.items()
                )
                old_ids = ",".join(str(old) for old in changes.keys())
                cursor.execute(f"""
                    UPDATE {schema}.core_pessoa
                    SET user_id = CASE user_id {case_clauses} END
                    WHERE user_id IN ({old_ids})
                """)
                rows = cursor.rowcount
                self.stdout.write(f"    {rows} pessoa(s) atualizada(s): {changes}")

            # Nova FK apontando para public.auth_user
            cursor.execute(f"""
                ALTER TABLE {schema}.core_pessoa
                ADD CONSTRAINT core_pessoa_user_id_fk_public_auth_user
                FOREIGN KEY (user_id) REFERENCES public.auth_user(id)
                ON DELETE SET NULL
                DEFERRABLE INITIALLY DEFERRED
            """)
            self.stdout.write(self.style.SUCCESS(f"    Nova FK -> public.auth_user criada"))

        # ============================================
        # STEP 3: Atualizar django_admin_log
        # ============================================
        self.stdout.write(self.style.MIGRATE_HEADING("\nSTEP 3: Atualizar django_admin_log"))

        for schema in tenant_schemas:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = 'django_admin_log'
                )
            """, [schema])
            if not cursor.fetchone()[0]:
                self.stdout.write(f"  {schema}: django_admin_log nao existe, pulando")
                continue

            # Buscar FK constraints
            cursor.execute(f"""
                SELECT conname FROM pg_constraint
                WHERE conrelid = '{schema}.django_admin_log'::regclass
                AND contype = 'f'
                AND (SELECT relname FROM pg_class WHERE oid = confrelid) = 'auth_user'
            """)
            constraints = cursor.fetchall()
            for (conname,) in constraints:
                cursor.execute(f"ALTER TABLE {schema}.django_admin_log DROP CONSTRAINT IF EXISTS {conname}")

            # Atualizar user_ids
            for old_id, new_id in mapping[schema].items():
                if old_id != new_id:
                    cursor.execute(f"""
                        UPDATE {schema}.django_admin_log SET user_id = %s WHERE user_id = %s
                    """, [new_id, old_id])

            # Nova FK para public
            cursor.execute(f"""
                ALTER TABLE {schema}.django_admin_log
                ADD CONSTRAINT django_admin_log_user_id_fk_public_auth_user
                FOREIGN KEY (user_id) REFERENCES public.auth_user(id)
                ON DELETE CASCADE
                DEFERRABLE INITIALLY DEFERRED
            """)
            self.stdout.write(f"  {schema}.django_admin_log -> atualizado")

        # ============================================
        # STEP 4: Atualizar django_session (se existir nos tenants)
        # ============================================
        self.stdout.write(self.style.MIGRATE_HEADING("\nSTEP 4: Limpar sessions dos tenants"))

        for schema in tenant_schemas:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = 'django_session'
                )
            """, [schema])
            if cursor.fetchone()[0]:
                cursor.execute(f"DELETE FROM {schema}.django_session")
                self.stdout.write(f"  {schema}.django_session -> limpo")

        # ============================================
        # STEP 5: Dropar tabelas auth dos tenants
        # ============================================
        self.stdout.write(self.style.MIGRATE_HEADING("\nSTEP 5: Dropar tabelas auth dos tenant schemas"))

        auth_tables = [
            'auth_user_user_permissions',
            'auth_user_groups',
            'auth_group_permissions',
            'auth_permission',
            'auth_group',
            'auth_user',
            'django_content_type',
        ]

        for schema in tenant_schemas:
            for table in auth_tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = %s AND table_name = %s
                    )
                """, [schema, table])
                if cursor.fetchone()[0]:
                    cursor.execute(f"DROP TABLE IF EXISTS {schema}.{table} CASCADE")
                    self.stdout.write(f"  DROP {schema}.{table}")

        # ============================================
        # STEP 6: Limpar migrations de auth/contenttypes dos tenants
        # ============================================
        self.stdout.write(self.style.MIGRATE_HEADING("\nSTEP 6: Limpar registros de migration"))

        for schema in tenant_schemas:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = 'django_migrations'
                )
            """, [schema])
            if cursor.fetchone()[0]:
                cursor.execute(f"""
                    DELETE FROM {schema}.django_migrations
                    WHERE app IN ('auth', 'contenttypes')
                """)
                rows = cursor.rowcount
                self.stdout.write(f"  {schema}: {rows} registros de migration removidos (auth/contenttypes)")

        self.stdout.write(self.style.SUCCESS("\n=== Migracao concluida com sucesso! ==="))
