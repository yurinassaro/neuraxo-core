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
    empresas_gestor = models.ManyToManyField(
        Empresa, related_name='gestores', blank=True,
        help_text='Empresas onde esta pessoa é gestora (nas demais é funcionário)',
    )
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True, related_name='pessoas')
    is_gestor = models.BooleanField(default=False, help_text='Legado - usar empresas_gestor')
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

    @property
    def eh_gestor(self):
        """True se é gestor de pelo menos uma empresa (substitui is_gestor global)"""
        return self.is_gestor or self.empresas_gestor.exists()

    def get_papel_empresa(self, empresa):
        """Retorna o papel nesta empresa: gestor, colaborador ou executante"""
        try:
            pe = self.papeis_empresa.get(empresa=empresa)
            return pe.papel
        except PapelEmpresa.DoesNotExist:
            pass
        # Fallback: empresas_gestor
        if self.empresas_gestor.filter(id=empresa.id).exists():
            return 'gestor'
        # Fallback: is_gestor global
        if self.is_gestor:
            return 'gestor'
        return 'executante'

    def is_gestor_empresa(self, empresa):
        """Verifica se é gestor de uma empresa"""
        return self.get_papel_empresa(empresa) == 'gestor'

    def pode_ver_equipe(self, empresa):
        """Gestor e colaborador veem tarefas de todos"""
        return self.get_papel_empresa(empresa) in ('gestor', 'colaborador')

    def pode_ver_financeiro(self, empresa):
        """Só gestor vê financeiro"""
        return self.get_papel_empresa(empresa) == 'gestor'

    def telefone_formatado(self):
        """Retorna telefone no formato para WAPI"""
        telefone = ''.join(filter(str.isdigit, self.telefone))
        if not telefone.startswith('55'):
            telefone = '55' + telefone
        return telefone


class PapelEmpresa(models.Model):
    """Define o papel de uma pessoa em cada empresa"""
    PAPEL_CHOICES = [
        ('gestor', 'Gestor'),
        ('colaborador', 'Colaborador'),
        ('executante', 'Executante'),
    ]
    pessoa = models.ForeignKey('Pessoa', on_delete=models.CASCADE, related_name='papeis_empresa')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='papeis_pessoas')
    papel = models.CharField(max_length=15, choices=PAPEL_CHOICES, default='executante')

    class Meta:
        verbose_name = 'Papel na Empresa'
        verbose_name_plural = 'Papéis nas Empresas'
        unique_together = ['pessoa', 'empresa']

    def __str__(self):
        return f"{self.pessoa.nome} - {self.empresa.nome} ({self.get_papel_display()})"


class NotificacaoInApp(models.Model):
    """Notificação in-app para o sininho na navbar"""
    TIPO_CHOICES = [
        ('demanda', 'Nova Demanda'),
        ('tarefa', 'Nova Tarefa'),
        ('comentario', 'Comentário'),
        ('prazo', 'Prazo Vencendo'),
        ('convite', 'Convite'),
        ('geral', 'Geral'),
    ]

    destinatario = models.ForeignKey('Pessoa', on_delete=models.CASCADE, related_name='notificacoes_inapp')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='geral')
    titulo = models.CharField(max_length=200)
    mensagem = models.CharField(max_length=500, blank=True)
    url = models.CharField(max_length=500, blank=True, help_text='URL para redirecionar ao clicar')
    lida = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{'[Lida]' if self.lida else '[Nova]'} {self.titulo} -> {self.destinatario.nome}"

    @classmethod
    def criar(cls, destinatario, tipo, titulo, mensagem='', url=''):
        """Helper para criar notificação"""
        return cls.objects.create(
            destinatario=destinatario,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            url=url,
        )


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


class StatusContrato(models.TextChoices):
    ATIVO = 'ativo', 'Ativo'
    PAUSADO = 'pausado', 'Pausado'
    INADIMPLENTE = 'inadimplente', 'Inadimplente'
    CANCELADO = 'cancelado', 'Cancelado'


class FormaPagamento(models.TextChoices):
    BOLETO = 'boleto', 'Boleto'
    PIX = 'pix', 'Pix'
    CARTAO = 'cartao', 'Cartão'
    TRANSFERENCIA = 'transferencia', 'Transferência'
    OUTRO = 'outro', 'Outro'


class SegmentoCliente(models.TextChoices):
    ECOMMERCE = 'ecommerce', 'E-commerce'
    CLINICA = 'clinica', 'Clínica / Saúde'
    RESTAURANTE = 'restaurante', 'Restaurante / Alimentação'
    INDUSTRIA = 'industria', 'Indústria'
    SERVICOS = 'servicos', 'Serviços'
    VAREJO = 'varejo', 'Varejo / Loja Física'
    EDUCACAO = 'educacao', 'Educação'
    IMOBILIARIA = 'imobiliaria', 'Imobiliária'
    OUTRO = 'outro', 'Outro'


class Cliente(models.Model):
    """Cliente de uma empresa"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='clientes', null=True, blank=True)
    nome = models.CharField(max_length=200, help_text='Nome fantasia')
    razao_social = models.CharField(max_length=300, blank=True, verbose_name='Razão Social')
    tipo = models.CharField(max_length=2, choices=TipoCliente.choices, default=TipoCliente.PESSOA_JURIDICA)
    cpf_cnpj = models.CharField(max_length=18, blank=True, verbose_name='CPF/CNPJ')
    inscricao_estadual = models.CharField(max_length=20, blank=True, verbose_name='Inscrição Estadual')
    inscricao_municipal = models.CharField(max_length=20, blank=True, verbose_name='Inscrição Municipal')
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    site = models.URLField(blank=True)
    endereco = models.CharField(max_length=300, blank=True, verbose_name='Endereço')
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True, verbose_name='UF')
    cep = models.CharField(max_length=9, blank=True, verbose_name='CEP')
    segmento = models.CharField(max_length=15, choices=SegmentoCliente.choices, default=SegmentoCliente.OUTRO, blank=True)

    # Contrato
    TIPO_CONTRATO_CHOICES = [
        ('mensal', 'Mensal'),
        ('quinzenal', 'Quinzenal'),
        ('projeto', 'Por Projeto'),
        ('avulso', 'Avulso / Sob demanda'),
    ]
    status_contrato = models.CharField(max_length=15, choices=StatusContrato.choices, default=StatusContrato.ATIVO)
    tipo_contrato = models.CharField(max_length=10, choices=TIPO_CONTRATO_CHOICES, default='mensal')
    valor_mensal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Fee mensal ou valor do projeto')
    dia_vencimento = models.IntegerField(null=True, blank=True, help_text='Dia do mês que vence (1-31)')
    forma_pagamento = models.CharField(max_length=15, choices=FormaPagamento.choices, default=FormaPagamento.BOLETO, blank=True)
    data_inicio_contrato = models.DateField(null=True, blank=True)
    data_renovacao = models.DateField(null=True, blank=True)

    # Serviços contratados
    servicos = models.TextField(blank=True, help_text='Serviços contratados (ex: Tráfego Pago, Social Media, Criativos)')

    # Gateway
    gateway_id = models.CharField(max_length=100, blank=True, help_text='ID no gateway de pagamento (Asaas, etc)')

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

    @property
    def status_badge(self):
        cores = {
            'ativo': ('bg-green-100 text-green-700', 'Ativo'),
            'pausado': ('bg-yellow-100 text-yellow-700', 'Pausado'),
            'inadimplente': ('bg-red-100 text-red-700', 'Inadimplente'),
            'cancelado': ('bg-gray-100 text-gray-500', 'Cancelado'),
        }
        return cores.get(self.status_contrato, ('bg-gray-100 text-gray-500', self.status_contrato))

    def get_pendencias_count(self):
        return self.solicitacoes.exclude(status__in=['concluido', 'cancelado']).count()

    def get_atrasadas_count(self):
        from django.utils import timezone
        return self.solicitacoes.filter(
            status__in=['pendente', 'em_andamento'],
            prazo__lt=timezone.now()
        ).count()


class ContatoCliente(models.Model):
    """Funcionário/contato dentro de uma empresa-cliente"""
    PAPEL_CHOICES = [
        ('dono', 'Dono / Responsável'),
        ('funcionario', 'Funcionário'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='contatos')
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='contato_cliente', help_text='User para login no portal')
    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, blank=True, verbose_name='CPF')
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True, help_text='WhatsApp / Celular')
    papel = models.CharField(max_length=15, choices=PAPEL_CHOICES, default='funcionario')
    funcao = models.CharField(max_length=100, blank=True, help_text='Ex: Criativo, Financeiro, TI')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Contato do Cliente'
        verbose_name_plural = 'Contatos dos Clientes'
        ordering = ['-papel', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.cliente.nome})"


class TipoSolicitacao(models.TextChoices):
    MATERIAL = 'material', 'Envio de Material'
    APROVACAO = 'aprovacao', 'Aprovação'
    BRIEFING = 'briefing', 'Briefing / Informações'
    DOCUMENTO = 'documento', 'Documento'
    PAGAMENTO = 'pagamento', 'Pagamento'
    OUTRO = 'outro', 'Outro'


class StatusSolicitacao(models.TextChoices):
    PENDENTE = 'pendente', 'Pendente'
    EM_ANDAMENTO = 'em_andamento', 'Em Andamento'
    CONCLUIDO = 'concluido', 'Concluído'
    ATRASADO = 'atrasado', 'Atrasado'
    CANCELADO = 'cancelado', 'Cancelado'


class Solicitacao(models.Model):
    """Solicitação feita ao cliente"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='solicitacoes')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='solicitacoes')
    contato = models.ForeignKey(ContatoCliente, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='solicitacoes', help_text='Pessoa específica que deve executar')
    criado_por = models.ForeignKey('Pessoa', on_delete=models.SET_NULL, null=True, related_name='solicitacoes_criadas')
    titulo = models.CharField(max_length=300)
    descricao = models.TextField(blank=True, help_text='Detalhes do que precisa')
    tipo = models.CharField(max_length=15, choices=TipoSolicitacao.choices, default=TipoSolicitacao.OUTRO)
    prazo = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=StatusSolicitacao.choices, default=StatusSolicitacao.PENDENTE)
    # Resposta do cliente
    resposta = models.TextField(blank=True)
    concluido_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Solicitação'
        verbose_name_plural = 'Solicitações'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.titulo} - {self.cliente.nome}"

    @property
    def esta_atrasada(self):
        if self.status in ('concluido', 'cancelado'):
            return False
        if self.prazo:
            from django.utils import timezone
            return timezone.now() > self.prazo
        return False


class ArquivoSolicitacao(models.Model):
    """Arquivo anexado a uma solicitação (pelo gestor ou pelo cliente)"""
    solicitacao = models.ForeignKey(Solicitacao, on_delete=models.CASCADE, related_name='arquivos')
    pasta = models.ForeignKey('PastaCliente', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='arquivos_solicitacao', help_text='Pasta onde o arquivo foi organizado')
    arquivo = models.FileField(upload_to='solicitacoes/%Y/%m/')
    nome_original = models.CharField(max_length=255)
    tamanho = models.IntegerField(default=0, help_text='Tamanho em bytes')
    enviado_por_cliente = models.BooleanField(default=False)
    enviado_por_nome = models.CharField(max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome_original

    @property
    def tamanho_formatado(self):
        if self.tamanho < 1024:
            return f"{self.tamanho} B"
        elif self.tamanho < 1024 * 1024:
            return f"{self.tamanho / 1024:.0f} KB"
        return f"{self.tamanho / (1024*1024):.1f} MB"

    @property
    def is_imagem(self):
        ext = self.nome_original.lower().split('.')[-1] if '.' in self.nome_original else ''
        return ext in ('jpg', 'jpeg', 'png', 'gif', 'webp', 'svg')


class ComentarioSolicitacao(models.Model):
    """Comentário/mensagem em uma solicitação (chat bidirecional)"""
    solicitacao = models.ForeignKey(Solicitacao, on_delete=models.CASCADE, related_name='comentarios')
    autor_nome = models.CharField(max_length=200)
    autor_is_cliente = models.BooleanField(default=False)
    texto = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em']

    def __str__(self):
        return f"{self.autor_nome}: {self.texto[:50]}"


class PastaTemplateEmpresa(models.Model):
    """Template de pastas que são criadas automaticamente para novos clientes"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='pastas_template')
    nome = models.CharField(max_length=100)
    ordem = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Template de Pasta'
        verbose_name_plural = 'Templates de Pastas'
        ordering = ['ordem', 'nome']
        unique_together = ['empresa', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.empresa.nome})"


class PastaCliente(models.Model):
    """Pasta de arquivos de um cliente"""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pastas')
    nome = models.CharField(max_length=100)
    pasta_pai = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subpastas')
    criada_por_cliente = models.BooleanField(default=False)
    ordem = models.IntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pasta do Cliente'
        verbose_name_plural = 'Pastas dos Clientes'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome

    def get_arquivos_count(self):
        return self.arquivos_pasta.count()

    def get_tamanho_total(self):
        total = sum(a.tamanho for a in self.arquivos_pasta.all())
        if total < 1024 * 1024:
            return f"{total / 1024:.0f} KB"
        return f"{total / (1024*1024):.1f} MB"


class ArquivoPasta(models.Model):
    """Arquivo dentro de uma pasta do cliente"""
    pasta = models.ForeignKey(PastaCliente, on_delete=models.CASCADE, related_name='arquivos_pasta')
    arquivo = models.FileField(upload_to='clientes/%Y/%m/')
    nome_original = models.CharField(max_length=255)
    tamanho = models.IntegerField(default=0)
    enviado_por = models.CharField(max_length=200, blank=True)
    enviado_por_cliente = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome_original

    @property
    def tamanho_formatado(self):
        if self.tamanho < 1024:
            return f"{self.tamanho} B"
        elif self.tamanho < 1024 * 1024:
            return f"{self.tamanho / 1024:.0f} KB"
        return f"{self.tamanho / (1024*1024):.1f} MB"

    @property
    def is_imagem(self):
        ext = self.nome_original.lower().split('.')[-1] if '.' in self.nome_original else ''
        return ext in ('jpg', 'jpeg', 'png', 'gif', 'webp', 'svg')

    @property
    def is_video(self):
        ext = self.nome_original.lower().split('.')[-1] if '.' in self.nome_original else ''
        return ext in ('mp4', 'mov', 'avi', 'mkv', 'webm')

    @property
    def is_pdf(self):
        return self.nome_original.lower().endswith('.pdf')

    @property
    def is_pdf(self):
        return self.nome_original.lower().endswith('.pdf')


class PastaEmpresa(models.Model):
    """Pasta de arquivos internos de uma empresa (Drive)"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='pastas_drive')
    nome = models.CharField(max_length=150)
    pasta_pai = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subpastas')
    criado_por = models.ForeignKey('Pessoa', on_delete=models.SET_NULL, null=True, blank=True)
    cor = models.CharField(max_length=7, default='#f59e0b', help_text='Cor do ícone da pasta')
    ordem = models.IntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pasta da Empresa'
        verbose_name_plural = 'Pastas das Empresas'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.empresa.nome})"

    def get_arquivos_count(self):
        return self.arquivos.count()

    def get_tamanho_total(self):
        total = sum(a.tamanho for a in self.arquivos.all())
        if total < 1024:
            return f"{total} B"
        elif total < 1024 * 1024:
            return f"{total / 1024:.0f} KB"
        return f"{total / (1024*1024):.1f} MB"


class ArquivoEmpresa(models.Model):
    """Arquivo dentro de uma pasta do Drive da empresa"""
    pasta = models.ForeignKey(PastaEmpresa, on_delete=models.CASCADE, related_name='arquivos')
    arquivo = models.FileField(upload_to='drive/%Y/%m/')
    nome_original = models.CharField(max_length=255)
    tamanho = models.IntegerField(default=0)
    enviado_por = models.ForeignKey('Pessoa', on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome_original

    @property
    def tamanho_formatado(self):
        if self.tamanho < 1024:
            return f"{self.tamanho} B"
        elif self.tamanho < 1024 * 1024:
            return f"{self.tamanho / 1024:.0f} KB"
        return f"{self.tamanho / (1024*1024):.1f} MB"

    @property
    def is_imagem(self):
        ext = self.nome_original.lower().rsplit('.', 1)[-1] if '.' in self.nome_original else ''
        return ext in ('jpg', 'jpeg', 'png', 'gif', 'webp', 'svg')

    @property
    def is_video(self):
        ext = self.nome_original.lower().rsplit('.', 1)[-1] if '.' in self.nome_original else ''
        return ext in ('mp4', 'mov', 'avi', 'mkv', 'webm')

    @property
    def is_pdf(self):
        return self.nome_original.lower().endswith('.pdf')

    @property
    def extensao(self):
        return self.nome_original.lower().rsplit('.', 1)[-1] if '.' in self.nome_original else ''


class CategoriaCofre(models.TextChoices):
    SITE = 'site', 'Site/Sistema'
    EMAIL = 'email', 'E-mail'
    BANCO = 'banco', 'Banco/Financeiro'
    API = 'api', 'Chave API'
    SERVIDOR = 'servidor', 'Servidor/Hosting'
    REDE_SOCIAL = 'social', 'Rede Social'
    OUTRO = 'outro', 'Outro'


class ItemCofre(models.Model):
    """Credencial armazenada no cofre de senhas"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='cofre_itens')
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, null=True, blank=True, related_name='cofre_itens',
                                 help_text='Cliente vinculado (opcional)')
    titulo = models.CharField(max_length=200)
    categoria = models.CharField(max_length=20, choices=CategoriaCofre.choices, default=CategoriaCofre.SITE)
    url = models.URLField(blank=True)
    usuario = models.CharField(max_length=200, blank=True)
    senha_encrypted = models.TextField(blank=True, help_text='Senha criptografada')
    notas = models.TextField(blank=True)
    criado_por = models.ForeignKey('Pessoa', on_delete=models.SET_NULL, null=True, related_name='cofre_criados')
    compartilhado_com = models.ManyToManyField('Pessoa', blank=True, related_name='cofre_compartilhados',
                                                help_text='Funcionarios que podem ver este item (vazio = somente criador e gestores)')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Item do Cofre'
        verbose_name_plural = 'Itens do Cofre'
        ordering = ['empresa', 'categoria', 'titulo']

    def __str__(self):
        return f"{self.titulo} ({self.empresa.nome})"

    def set_senha(self, raw_password):
        """Criptografa e salva a senha usando Fernet"""
        if not raw_password:
            self.senha_encrypted = ''
            return
        from cryptography.fernet import Fernet
        from django.conf import settings
        import base64, hashlib
        key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
        f = Fernet(key)
        self.senha_encrypted = f.encrypt(raw_password.encode()).decode()

    def get_senha(self):
        """Descriptografa e retorna a senha"""
        if not self.senha_encrypted:
            return ''
        try:
            from cryptography.fernet import Fernet
            from django.conf import settings
            import base64, hashlib
            key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
            f = Fernet(key)
            return f.decrypt(self.senha_encrypted.encode()).decode()
        except Exception:
            return '***erro ao descriptografar***'
