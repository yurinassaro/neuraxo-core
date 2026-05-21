from django.db import models
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


class Client(models.Model):
    """
    Registro legado de tenants (mantido para referência/histórico).
    O sistema agora usa schema único com isolamento por Empresa.
    """
    nome = models.CharField(max_length=200)
    schema_name = models.CharField(max_length=63, unique=True)
    admin_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenants_admin',
        verbose_name='Administrador',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tenant (legado)'
        verbose_name_plural = 'Tenants (legado)'
        managed = False  # Não gerenciar esta tabela (já existe)
        db_table = 'tenants_client'

    def __str__(self):
        return self.nome


class Domain(models.Model):
    """Registro legado de domínios (mantido para referência)."""
    domain = models.CharField(max_length=253)
    tenant = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='domains')
    is_primary = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'tenants_domain'

    def __str__(self):
        return self.domain
