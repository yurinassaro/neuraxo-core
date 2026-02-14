from django.db import models
from django.contrib.auth.models import User


class Empresa(models.Model):
    """Empresa - Ex: Neuraxo, Tarragona, Ailote, Anac, Pessoal"""
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    cor = models.CharField(max_length=7, default='#6366f1', help_text='Cor em hex para identificação visual')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nome']

    def __str__(self):
        return self.nome


# Alias para compatibilidade com código existente
Workspace = Empresa


class Cargo(models.Model):
    """Cargo/Função com processos documentados"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='cargos', null=True, blank=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, help_text='Descrição geral do cargo')
    processos = models.TextField(blank=True, help_text='Documentação dos processos desta função')
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        ordering = ['empresa', 'nome']
        unique_together = ['empresa', 'nome']

    def __str__(self):
        if self.empresa:
            return f"{self.nome} ({self.empresa.nome})"
        return self.nome

    # Alias para compatibilidade
    @property
    def workspace(self):
        return self.empresa


class Pessoa(models.Model):
    """Funcionário/Colaborador"""
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nome = models.CharField(max_length=200)
    telefone = models.CharField(max_length=20, help_text='WhatsApp com DDD - Ex: 5511999999999')
    email = models.EmailField(blank=True)
    empresas = models.ManyToManyField(Empresa, related_name='pessoas', blank=True)
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True, related_name='pessoas')
    is_gestor = models.BooleanField(default=False, help_text='Gestor pode ver tarefas de todos e criar demandas')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    # Preferências de notificação
    receber_lembretes = models.BooleanField(default=True)
    horario_lembrete = models.TimeField(default='08:00', help_text='Horário do lembrete diário')
    empresas_lembrete_financeiro = models.ManyToManyField(
        Empresa,
        related_name='pessoas_lembrete_financeiro',
        blank=True,
        help_text='Empresas das quais recebe lembrete de contas a pagar via WhatsApp'
    )

    # Alias para compatibilidade
    @property
    def workspaces(self):
        return self.empresas

    class Meta:
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def telefone_formatado(self):
        """Retorna telefone no formato para WAPI"""
        telefone = ''.join(filter(str.isdigit, self.telefone))
        if not telefone.startswith('55'):
            telefone = '55' + telefone
        return telefone


class PessoaExterna(models.Model):
    """Contato externo reutilizável para dependências"""
    nome = models.CharField(max_length=200)
    telefone = models.CharField(max_length=20, blank=True, help_text='WhatsApp com DDD')
    empresa_nome = models.CharField(max_length=200, blank=True, help_text='Empresa do contato')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pessoa Externa'
        verbose_name_plural = 'Pessoas Externas'
        ordering = ['nome']

    def __str__(self):
        if self.empresa_nome:
            return f"{self.nome} ({self.empresa_nome})"
        return self.nome


class TipoCliente(models.TextChoices):
    PESSOA_FISICA = 'pf', 'Pessoa Física'
    PESSOA_JURIDICA = 'pj', 'Pessoa Jurídica'


class Cliente(models.Model):
    """Cliente para projetos"""
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=2, choices=TipoCliente.choices, default=TipoCliente.PESSOA_JURIDICA)
    cpf_cnpj = models.CharField(max_length=18, blank=True, verbose_name='CPF/CNPJ')
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    endereco = models.TextField(blank=True, verbose_name='Endereço')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def get_projetos_ativos(self):
        return self.projetos.exclude(status__in=['concluido', 'cancelado'])
