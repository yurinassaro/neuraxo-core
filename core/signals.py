from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='core.Empresa')
def vincular_empresa_ao_admin(sender, instance, created, **kwargs):
    """Ao criar uma nova Empresa, vincula automaticamente ao admin principal (user.is_superuser)."""
    if not created:
        return

    from core.models import Pessoa
    admin = Pessoa.objects.filter(user__is_superuser=True, ativo=True).first()
    if admin:
        admin.empresas.add(instance)
