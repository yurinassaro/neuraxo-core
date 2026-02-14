import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_tenants.utils import tenant_context

logger = logging.getLogger(__name__)

# Permissões por grupo (app_label.codename)
GRUPO_PERMISSOES = {
    'Administrador': {
        # Tudo de core
        'core': ['add', 'change', 'delete', 'view'],
        # Tudo de checklists
        'checklists': ['add', 'change', 'delete', 'view'],
        # Tudo de financeiro
        'financeiro': ['add', 'change', 'delete', 'view'],
        # Tudo de notifications
        'notifications': ['add', 'change', 'delete', 'view'],
        # Gerenciar usuários
        'auth': ['add', 'change', 'delete', 'view'],
    },
    'Gerente': {
        'core': ['add', 'change', 'view'],
        'checklists': ['add', 'change', 'delete', 'view'],
        'financeiro': ['view'],
        'notifications': ['add', 'change', 'view'],
        'auth': ['view'],
    },
    'Funcionário': {
        'core': ['view'],
        'checklists': ['change', 'view'],
        'financeiro': [],
        'notifications': ['view'],
        'auth': [],
    },
}


def _create_permission_groups(tenant):
    """Cria os grupos de permissão padrão dentro do schema do tenant."""
    from django.contrib.auth.models import Group, Permission

    with tenant_context(tenant):
        for grupo_nome, apps_perms in GRUPO_PERMISSOES.items():
            group, _ = Group.objects.get_or_create(name=grupo_nome)
            perms = []
            for app_label, actions in apps_perms.items():
                if not actions:
                    continue
                codename_prefixes = [f'{a}_' for a in actions]
                for perm in Permission.objects.filter(
                    content_type__app_label=app_label
                ):
                    if any(perm.codename.startswith(p) for p in codename_prefixes):
                        perms.append(perm)
            group.permissions.set(perms)
            logger.info(
                'Grupo "%s" criado para tenant "%s" com %d permissões',
                grupo_nome, tenant.schema_name, len(perms),
            )


@receiver(post_save, sender='tenants.Client')
def create_tenant_initial_data(sender, instance, created, **kwargs):
    """Cria superusuário admin e grupos de permissão ao criar um novo tenant."""
    if not created:
        return
    if instance.schema_name == 'public':
        return

    from django.contrib.auth import get_user_model
    User = get_user_model()

    slug = instance.schema_name.lower().replace(' ', '_')
    username = f'admin.{slug}'
    default_password = 'neuraxo@2026'

    try:
        with tenant_context(instance):
            # Criar superusuário
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(
                    username=username,
                    email=f'admin@{slug}.neuraxo.com.br',
                    password=default_password,
                )
                logger.info(
                    'Superusuário "%s" criado para tenant "%s"',
                    username, instance.schema_name,
                )

        # Criar grupos de permissão
        _create_permission_groups(instance)

    except Exception as e:
        logger.error(
            'Erro ao configurar tenant "%s": %s',
            instance.schema_name, e,
        )
