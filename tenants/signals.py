import logging
from django.contrib.auth.models import Group, Permission

logger = logging.getLogger(__name__)

# Permissões por grupo (app_label.codename)
GRUPO_PERMISSOES = {
    'Administrador': {
        'core': ['add', 'change', 'delete', 'view'],
        'checklists': ['add', 'change', 'delete', 'view'],
        'financeiro': ['add', 'change', 'delete', 'view'],
        'notifications': ['add', 'change', 'delete', 'view'],
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


def create_permission_groups():
    """Cria os grupos de permissão padrão."""
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
        logger.info('Grupo "%s" configurado com %d permissões', grupo_nome, len(perms))
