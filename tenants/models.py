from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_tenants.models import TenantMixin, DomainMixin
from django.contrib.auth.models import User


# ============================================
# TEMPLATE DE PROJETO GLOBAL (Schema Público)
# ============================================

class ProjetoTemplateGlobal(models.Model):
    """
    Template de PROJETO global - pode ser vinculado a tenants específicos.
    Fica no schema público e pode ser usado para criar projetos nos tenants selecionados.
    """
    titulo = models.CharField(max_length=300)
    descricao = models.TextField(blank=True)
    cor = models.CharField(max_length=7, default='#6366f1', help_text='Cor em hex')

    # Tenants vinculados (checkbox no admin)
    tenants = models.ManyToManyField(
        'Client',
        blank=True,
        related_name='templates_projeto_globais',
        help_text='Selecione os tenants que poderão usar este template de projeto'
    )

    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Template de Projeto Global'
        verbose_name_plural = 'Templates de Projeto Globais'
        ordering = ['titulo']

    def __str__(self):
        return f"[GLOBAL] {self.titulo}"

    def get_total_etapas(self):
        return self.etapas.count()

    def get_tenants_display(self):
        """Retorna lista de tenants vinculados"""
        tenants = self.tenants.exclude(schema_name='public')
        if not tenants:
            return "Nenhum tenant"
        return ", ".join([t.nome for t in tenants])


class EtapaTemplateGlobal(models.Model):
    """Etapa dentro de um template de projeto global"""
    template = models.ForeignKey(ProjetoTemplateGlobal, on_delete=models.CASCADE, related_name='etapas')
    titulo = models.CharField(max_length=300)
    descricao = models.TextField(blank=True)
    ordem = models.IntegerField(default=0)
    tempo_estimado = models.IntegerField(null=True, blank=True, help_text='Tempo estimado em minutos')

    class Meta:
        verbose_name = 'Etapa do Template Global'
        verbose_name_plural = 'Etapas do Template Global'
        ordering = ['ordem', 'id']

    def __str__(self):
        return f"{self.ordem}. {self.titulo}"


class Client(TenantMixin):
    """
    Tenant = Cliente do SaaS (ex: Grupo Yuri, Clinica Silva).
    Cada tenant tem seu proprio schema PostgreSQL com dados isolados.
    """
    nome = models.CharField(max_length=200)
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    # django-tenants: auto_create_schema cria o schema ao salvar
    auto_create_schema = True

    class Meta:
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    def __str__(self):
        return self.nome


class Domain(DomainMixin):
    """
    Dominio associado a um tenant.
    Ex: grupoyuri.core.neuraxo.com.br -> tenant "Grupo Yuri"
    """
    pass


# ============================================
# ACESSO COMPARTILHADO (Schema Público)
# ============================================

class AcessoCompartilhado(models.Model):
    """
    Permite que um usuário de um tenant acesse outro tenant.
    Ex: admin.grupo_ronaldo pode acessar empresas do grupo_yuri.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='acessos_compartilhados',
    )
    tenant_destino = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='acessos_recebidos',
        help_text='Tenant que o usuário poderá acessar',
    )
    is_gestor = models.BooleanField(
        default=False,
        help_text='Se marcado, o usuário terá permissões de gestor no tenant destino',
    )
    empresas_ids = models.JSONField(
        default=list,
        blank=True,
        help_text='IDs das empresas permitidas no tenant destino (vazio = nenhuma)',
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Acesso Compartilhado'
        verbose_name_plural = 'Acessos Compartilhados'
        unique_together = ['user', 'tenant_destino']

    def __str__(self):
        return f"{self.user.username} → {self.tenant_destino.nome} ({'Gestor' if self.is_gestor else 'Funcionário'})"

    def get_empresas_display(self):
        """Retorna nomes das empresas permitidas"""
        if not self.empresas_ids:
            return "Nenhuma"
        from django_tenants.utils import schema_context
        from core.models import Empresa
        with schema_context(self.tenant_destino.schema_name):
            empresas = Empresa.objects.filter(id__in=self.empresas_ids, ativo=True)
            return ", ".join([e.nome for e in empresas])

    def sincronizar_pessoa(self):
        """Cria ou atualiza Pessoa no tenant destino com as empresas permitidas"""
        from django_tenants.utils import schema_context
        from core.models import Pessoa, Empresa

        with schema_context(self.tenant_destino.schema_name):
            pessoa, created = Pessoa.objects.get_or_create(
                user=self.user,
                defaults={
                    'nome': self.user.get_full_name() or self.user.username,
                    'email': self.user.email,
                    'is_gestor': self.is_gestor,
                    'ativo': self.ativo,
                }
            )

            if not created:
                pessoa.is_gestor = self.is_gestor
                pessoa.ativo = self.ativo
                pessoa.save(update_fields=['is_gestor', 'ativo'])

            # Sincronizar empresas permitidas
            if self.empresas_ids:
                empresas_permitidas = Empresa.objects.filter(
                    id__in=self.empresas_ids, ativo=True
                )
                pessoa.empresas.set(empresas_permitidas)
            else:
                pessoa.empresas.clear()

        return pessoa


@receiver(post_save, sender=AcessoCompartilhado)
def sincronizar_acesso(sender, instance, **kwargs):
    """Ao criar/atualizar um acesso compartilhado, sincroniza a Pessoa no tenant destino"""
    try:
        instance.sincronizar_pessoa()
    except Exception as e:
        print(f"[AcessoCompartilhado] Erro ao sincronizar: {e}")


@receiver(post_save, sender=Client)
def criar_admin_tenant(sender, instance, created, **kwargs):
    """
    Ao criar um novo tenant, cria automaticamente:
    1. Um usuario admin para o tenant
    2. Uma Pessoa associada com is_gestor=True

    Nota: Este signal pode falhar se as tabelas ainda não existirem.
    Nesse caso, o admin deve ser criado manualmente após as migrations.
    """
    if created and instance.schema_name != 'public':
        try:
            from django.db import connection
            from django_tenants.utils import schema_context

            # Gerar username baseado no schema
            username = f"admin.{instance.schema_name.lower()}"
            email = f"admin@{instance.schema_name.lower()}.neuraxo.com.br"

            # Verificar se usuario ja existe
            if not User.objects.filter(username=username).exists():
                # Criar usuario admin
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='mudar123',  # Senha padrao - deve ser alterada
                    is_staff=True,
                    is_superuser=True,
                )

                # Criar Pessoa no schema do tenant
                with schema_context(instance.schema_name):
                    from core.models import Pessoa, Empresa

                    # Criar empresa padrao
                    empresa, _ = Empresa.objects.get_or_create(
                        nome=instance.nome,
                        defaults={'cor': '#4f46e5', 'ativo': True}
                    )

                    # Criar pessoa admin
                    pessoa = Pessoa.objects.create(
                        nome='Administrador',
                        email=email,
                        user=user,
                        is_gestor=True,
                        ativo=True,
                    )
                    pessoa.empresas.add(empresa)

                print(f"[Tenant] Admin criado para {instance.nome}: {username} (senha: mudar123)")
        except Exception as e:
            print(f"[Tenant] Aviso: Não foi possível criar admin automaticamente para {instance.nome}: {e}")
            print("[Tenant] Execute 'python manage.py setup_tenant_admin' após as migrations.")
