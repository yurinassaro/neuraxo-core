"""
Migra todos os dados dos schemas de tenant para o schema público.
Usa INSERT genérico baseado nas colunas reais de cada tabela.

Uso:
    python manage.py migrar_para_public --dry-run
    python manage.py migrar_para_public
"""

from django.core.management.base import BaseCommand
from django.db import connection
from tenants.models import Client


# Ordem de migração (respeita ForeignKeys)
TABELAS_ORDEM = [
    'core_empresa',
    'core_cargo',
    'core_pessoa',
    'core_pessoa_empresas',
    'core_pessoa_empresas_lembrete_financeiro',
    'core_cliente',
    'core_pessoaexterna',
    'financeiro_categorialancamento',
    'financeiro_contabancaria',
    'financeiro_metaempresa',
    'financeiro_configmercadopago',
    'financeiro_lancamento',
    'financeiro_contapagar',
    'financeiro_contapagaritem',
    'financeiro_prestacaoconta',
    'financeiro_contareceber',
    'financeiro_contareceberitem',
    'financeiro_alertafinanceiro',
    'financeiro_alertafinanceiro_destinatarios',
    'financeiro_historicoalerta',
    'financeiro_historicoalerta_enviado_para',
    'checklists_checklisttemplate',
    'checklists_etapatemplate',
    'checklists_projetotemplate',
    'checklists_projeto',
    'checklists_projeto_participantes',
    'checklists_checklistitem',
    'checklists_subtarefa',
    'checklists_subtarefatemplate',
    'checklists_demanda',
    'checklists_subtarefademanda',
    'checklists_anexodemanda',
    'checklists_comentariodemanda',
    'checklists_aproveitamentodiario',
    'checklists_tarefanaoconcluida',
    'checklists_mapamentalno',
    'checklists_anotacao',
    'core_itemcofre',
    'notifications_agendamentonotificacao',
    'notifications_notificacaowhatsapp',
]

# Colunas FK que precisam ser remapeadas: coluna -> tabela referenciada
FK_REMAP = {
    'empresa_id': 'core_empresa',
    'pessoa_id': 'core_pessoa',
    'responsavel_id': 'core_pessoa',
    'criado_por_id': 'core_pessoa',
    'concluido_por_id': 'core_pessoa',
    'registrado_por_id': 'core_pessoa',
    'autor_id': 'core_pessoa',
    'cliente_id': 'core_pessoa',
    'cargo_id': 'core_cargo',
    'template_id': 'checklists_checklisttemplate',
    'etapa_id': 'checklists_etapatemplate',
    'projeto_id': 'checklists_projeto',
    'item_id': 'checklists_checklistitem',
    'checklist_item_id': 'checklists_checklistitem',
    'demanda_id': 'checklists_demanda',
    'aproveitamento_id': 'checklists_aproveitamentodiario',
    'categoria_id': 'financeiro_categorialancamento',
    'conta_id': 'financeiro_contabancaria',
    'conta_pagar_id': 'financeiro_contapagar',
    'lancamento_id': 'financeiro_lancamento',
    'conta_receber_id': 'financeiro_contareceber',
    'alerta_id': 'financeiro_alertafinanceiro',
    'conta_pagar_item_id': 'financeiro_contapagaritem',
    'conta_receber_item_id': 'financeiro_contareceberitem',
    'alertafinanceiro_id': 'financeiro_alertafinanceiro',
    'historicoalerta_id': 'financeiro_historicoalerta',
    'projeto_template_id': 'checklists_projetotemplate',
}

# Tabelas com dedup: (tabela, colunas_chave_unica)
# Se já existe registro com mesmos valores nessas colunas, reusar
DEDUP_KEYS = {
    'core_empresa': ['nome'],
    'core_cargo': ['nome'],
    'core_pessoa': ['user_id'],  # Dedup por user_id (pode ser null)
    'core_pessoa_empresas': ['pessoa_id', 'empresa_id'],
    'core_pessoa_empresas_lembrete_financeiro': ['pessoa_id', 'empresa_id'],
    'financeiro_categorialancamento': ['nome', 'empresa_id'],
}


class Command(BaseCommand):
    help = 'Migra dados de schemas tenant para o schema público'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        # {schema: {tabela: {old_id: new_id}}}
        self.id_maps = {}

        if self.dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN ==='))

        schemas = self._get_schemas()
        self.stdout.write(f'Schemas: {schemas}\n')

        for schema in schemas:
            self.stdout.write(self.style.MIGRATE_HEADING(f'\n=== {schema} ==='))
            self.id_maps[schema] = {}
            self._migrar_schema(schema)

        self._resumo()

    def _get_schemas(self):
        schemas = []
        for t in Client.objects.exclude(schema_name='public'):
            cursor = connection.cursor()
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name=%s)",
                [t.schema_name]
            )
            if cursor.fetchone()[0]:
                schemas.append(t.schema_name)
        return schemas

    def _migrar_schema(self, schema):
        for tabela in TABELAS_ORDEM:
            try:
                # Verificar se tabela existe no schema
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema=%s AND table_name=%s)",
                    [schema, tabela]
                )
                if not cursor.fetchone()[0]:
                    continue

                count = self._migrar_tabela(schema, tabela)
                if count > 0:
                    self.stdout.write(self.style.SUCCESS(f'  {tabela}: {count}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ERRO {tabela}: {e}'))

    def _migrar_tabela(self, schema, tabela):
        cursor = connection.cursor()

        # Ler dados do schema tenant
        cursor.execute(f'SET search_path TO "{schema}"')
        cursor.execute(f'SELECT * FROM {tabela} ORDER BY id')
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        cursor.execute('SET search_path TO public')

        if not rows:
            return 0

        count = 0
        has_id = 'id' in columns

        for row in rows:
            data = dict(zip(columns, row))

            # Remapear FKs
            for col in columns:
                if col in FK_REMAP and data.get(col) is not None:
                    ref_table = FK_REMAP[col]
                    mapped = self.id_maps.get(schema, {}).get(ref_table, {}).get(data[col])
                    if mapped is not None:
                        data[col] = mapped
                    # Se não tem mapeamento, manter o valor original (pode já existir no public)

            old_id = data.get('id')

            # Verificar dedup
            if tabela in DEDUP_KEYS and has_id:
                dedup_cols = DEDUP_KEYS[tabela]
                where_parts = []
                where_vals = []
                skip_dedup = False
                for dc in dedup_cols:
                    val = data.get(dc)
                    if val is None:
                        # Para user_id=None, não fazer dedup (pessoa sem user)
                        if dc == 'user_id':
                            skip_dedup = True
                            break
                        where_parts.append(f'{dc} IS NULL')
                    else:
                        where_parts.append(f'{dc} = %s')
                        where_vals.append(val)

                if not skip_dedup and where_parts:
                    cursor.execute(
                        f"SELECT id FROM public.{tabela} WHERE {' AND '.join(where_parts)} LIMIT 1",
                        where_vals
                    )
                    existing = cursor.fetchone()
                    if existing:
                        if has_id and old_id is not None:
                            self._store_map(schema, tabela, old_id, existing[0])
                        continue

            # Preparar INSERT (sem coluna id, deixar autoincrement)
            insert_cols = [c for c in columns if c != 'id']
            insert_vals = [data[c] for c in insert_cols]

            if self.dry_run:
                if has_id and old_id is not None:
                    self._store_map(schema, tabela, old_id, old_id)
                count += 1
                continue

            placeholders = ', '.join(['%s'] * len(insert_cols))
            cols_str = ', '.join(f'"{c}"' for c in insert_cols)

            if has_id:
                cursor.execute(
                    f'INSERT INTO public.{tabela} ({cols_str}) VALUES ({placeholders}) RETURNING id',
                    insert_vals
                )
                new_id = cursor.fetchone()[0]
                if old_id is not None:
                    self._store_map(schema, tabela, old_id, new_id)
            else:
                cursor.execute(
                    f'INSERT INTO public.{tabela} ({cols_str}) VALUES ({placeholders})',
                    insert_vals
                )

            count += 1

        return count

    def _store_map(self, schema, table, old_id, new_id):
        if table not in self.id_maps[schema]:
            self.id_maps[schema][table] = {}
        self.id_maps[schema][table][old_id] = new_id

    def _resumo(self):
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== RESUMO ==='))
        for schema, tables in self.id_maps.items():
            total = sum(len(m) for m in tables.values())
            self.stdout.write(f'\n  {schema}: {total} registros total')
            for table, mapping in sorted(tables.items()):
                self.stdout.write(f'    {table}: {len(mapping)}')

        if not self.dry_run:
            self.stdout.write(self.style.MIGRATE_HEADING('\n=== CONTAGENS PUBLIC ==='))
            cursor = connection.cursor()
            for t in ['core_empresa', 'core_pessoa', 'checklists_demanda',
                       'checklists_checklistitem', 'checklists_checklisttemplate',
                       'checklists_projeto', 'financeiro_lancamento', 'financeiro_contapagar']:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM public.{t}')
                    self.stdout.write(f'  {t}: {cursor.fetchone()[0]}')
                except Exception:
                    pass
