from django.db import models
from django.utils import timezone
from core.models import Empresa, Workspace, Pessoa, Cargo, Cliente


class Recorrencia(models.TextChoices):
    DIARIA = 'diaria', 'Diária'
    SEMANAL = 'semanal', 'Semanal'
    QUINZENAL = 'quinzenal', 'Quinzenal'
    MENSAL = 'mensal', 'Mensal'
    TRIMESTRAL = 'trimestral', 'Trimestral'
    SEMESTRAL = 'semestral', 'Semestral'
    ANUAL = 'anual', 'Anual'


class DiaSemana(models.IntegerChoices):
    SEGUNDA = 0, 'Segunda-feira'
    TERCA = 1, 'Terça-feira'
    QUARTA = 2, 'Quarta-feira'
    QUINTA = 3, 'Quinta-feira'
    SEXTA = 4, 'Sexta-feira'
    SABADO = 5, 'Sábado'
    DOMINGO = 6, 'Domingo'


class ChecklistTemplate(models.Model):
    """Template de tarefa recorrente - Rotina Diária"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='checklists', null=True, blank=True)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, help_text='Descrição detalhada da tarefa')
    processo = models.TextField(blank=True, help_text='Passo a passo de como executar')

    # Recorrência
    recorrencia = models.CharField(max_length=20, choices=Recorrencia.choices, default=Recorrencia.DIARIA)
    dia_semana = models.IntegerField(choices=DiaSemana.choices, null=True, blank=True,
                                      help_text='Para tarefas semanais - qual dia da semana')
    dia_mes = models.IntegerField(null=True, blank=True,
                                   help_text='Para tarefas mensais - qual dia do mês (1-31)')
    dias_semana_ativos = models.CharField(max_length=20, default='0,1,2,3,4',
                                           help_text='Dias da semana ativos (0=Seg, 1=Ter, 2=Qua, 3=Qui, 4=Sex, 5=Sáb, 6=Dom)')

    # Atribuição
    responsavel = models.ForeignKey(Pessoa, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='checklists_responsavel',
                                     help_text='Pessoa específica responsável')
    responsavel_todos = models.BooleanField(default=False,
                                             help_text='Atribuir a TODOS os funcionários')
    cargo_responsavel = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='checklists',
                                           help_text='Ou atribuir a todos do cargo')

    # Ordem de execução na rotina diária
    ordem_execucao = models.IntegerField(default=0, help_text='Ordem na lista de rotina diária (menor = primeiro)')

    # Tempo estimado (em minutos) - rotina diária, máx 4h
    TEMPO_ESTIMADO_CHOICES = [
        (0, 'Não definido'),
        (15, '15 minutos'),
        (30, '30 minutos'),
        (45, '45 minutos'),
        (60, '1 hora'),
        (90, '1h30'),
        (120, '2 horas'),
        (180, '3 horas'),
        (240, '4 horas'),
    ]
    tempo_estimado = models.IntegerField(default=0, choices=TEMPO_ESTIMADO_CHOICES,
                                          help_text='Tempo máximo estimado para conclusão')

    # Configurações
    prioridade = models.IntegerField(default=1, choices=[(1, 'Baixa'), (2, 'Média'), (3, 'Alta')])
    ativo = models.BooleanField(default=True)
    enviar_lembrete = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rotina Diária'
        verbose_name_plural = 'Rotinas Diárias'
        ordering = ['ordem_execucao', '-prioridade', 'titulo']

    def __str__(self):
        return f"{self.titulo} ({self.get_recorrencia_display()})"

    # Alias para compatibilidade
    @property
    def workspace(self):
        return self.empresa


class SubTarefaTemplate(models.Model):
    """Subtarefa padrão de um template - copiada ao gerar ChecklistItem"""
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.CASCADE, related_name='subtarefas_template')
    titulo = models.CharField(max_length=200)
    ordem = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Subtarefa do Template'
        verbose_name_plural = 'Subtarefas do Template'
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.titulo


class StatusItem(models.TextChoices):
    PENDENTE = 'pendente', 'Pendente'
    EM_ANDAMENTO = 'em_andamento', 'Em Andamento'
    DEPENDENTE = 'dependente', 'Aguardando Dependência'
    CONCLUIDO = 'concluido', 'Concluído'
    ATRASADO = 'atrasado', 'Atrasado'
    CANCELADO = 'cancelado', 'Cancelado'


class ChecklistItem(models.Model):
    """Instância de checklist gerada para um período específico"""
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.CASCADE, related_name='items')
    responsavel = models.ForeignKey(Pessoa, on_delete=models.SET_NULL, null=True, related_name='checklist_items')

    # Período
    data_referencia = models.DateField(help_text='Data de referência desta tarefa')
    data_limite = models.DateTimeField(help_text='Prazo para conclusão')

    # Ordem de execução (herda do template, mas pode ser customizada por dia)
    ordem = models.IntegerField(default=0, help_text='Ordem de execução na rotina do dia')

    # Descrição e Processo (pode sobrescrever o do template)
    descricao = models.TextField(blank=True, help_text='Descrição específica desta tarefa (sobrescreve o template)')
    processo = models.TextField(blank=True, help_text='Processo específico desta tarefa (sobrescreve o template)')

    # Status
    status = models.CharField(max_length=20, choices=StatusItem.choices, default=StatusItem.PENDENTE)
    concluido_em = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True, help_text='Observações do responsável')
    anotacoes = models.TextField(blank=True, help_text='Anotações durante a execução')

    # Justificativa (quando não concluir)
    justificativa = models.TextField(blank=True, help_text='Motivo por não ter concluído a tarefa')
    dia_fechado = models.BooleanField(default=False, help_text='Se o dia foi fechado para esta tarefa')

    # Dependência
    dependente_de = models.ForeignKey(Pessoa, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='tarefas_dependentes',
                                       help_text='Pessoa de quem esta tarefa depende')
    dependente_externo = models.CharField(max_length=200, blank=True,
                                           help_text='Nome de pessoa externa (não cadastrada no sistema)')
    telefone_dependente_externo = models.CharField(max_length=20, blank=True,
                                                     help_text='WhatsApp da pessoa externa')
    motivo_dependencia = models.CharField(max_length=500, blank=True,
                                           help_text='Motivo da dependência (ex: Aguardando aprovação do João)')
    dependencia_resolvida_em = models.DateTimeField(null=True, blank=True)

    # Timer de execução
    iniciado_em = models.DateTimeField(null=True, blank=True, help_text='Quando a tarefa foi iniciada pela primeira vez')
    timer_inicio = models.DateTimeField(null=True, blank=True, help_text='Quando o timer foi iniciado')
    timer_acumulado = models.IntegerField(default=0, help_text='Tempo acumulado em segundos')
    timer_ativo = models.BooleanField(default=False, help_text='Se o timer está rodando')

    # Cancelamento
    cancelamento_solicitado = models.BooleanField(default=False, help_text='Funcionário solicitou cancelamento')
    cancelamento_motivo = models.CharField(max_length=500, blank=True)

    # Tracking
    criado_em = models.DateTimeField(auto_now_add=True)
    lembrete_enviado = models.BooleanField(default=False)
    cobranca_enviada = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Item de Checklist'
        verbose_name_plural = 'Itens de Checklist'
        ordering = ['ordem', '-data_referencia', 'template__prioridade']
        unique_together = ['template', 'responsavel', 'data_referencia']

    def __str__(self):
        return f"{self.template.titulo} - {self.data_referencia}"

    def iniciar_timer(self):
        """Inicia ou continua o timer"""
        if not self.timer_ativo:
            agora = timezone.now()
            self.timer_inicio = agora
            self.timer_ativo = True
            # Registra quando a tarefa foi iniciada pela primeira vez
            if not self.iniciado_em:
                self.iniciado_em = agora
            if self.status == StatusItem.PENDENTE:
                self.status = StatusItem.EM_ANDAMENTO
            self.save()

    def pausar_timer(self):
        """Pausa o timer e acumula o tempo"""
        if self.timer_ativo and self.timer_inicio:
            delta = timezone.now() - self.timer_inicio
            self.timer_acumulado += int(delta.total_seconds())
            self.timer_ativo = False
            self.timer_inicio = None
            self.save()

    def get_tempo_total(self):
        """Retorna o tempo total em segundos (acumulado + atual se ativo)"""
        total = self.timer_acumulado
        if self.timer_ativo and self.timer_inicio:
            delta = timezone.now() - self.timer_inicio
            total += int(delta.total_seconds())
        return total

    def get_tempo_formatado(self):
        """Retorna o tempo formatado como HH:MM:SS"""
        total = self.get_tempo_total()
        horas = total // 3600
        minutos = (total % 3600) // 60
        segundos = total % 60
        if horas > 0:
            return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        return f"{minutos:02d}:{segundos:02d}"

    def marcar_concluido(self):
        """Marca o item como concluído e para o timer"""
        self.pausar_timer()  # Para o timer se estiver rodando
        self.status = StatusItem.CONCLUIDO
        self.concluido_em = timezone.now()
        self.save()

    def esta_atrasado(self):
        """Verifica se o item está atrasado"""
        if self.status == StatusItem.CONCLUIDO:
            return False
        return timezone.now() > self.data_limite

    def atualizar_status_atraso(self):
        """Atualiza status para atrasado se passou do prazo"""
        if self.esta_atrasado() and self.status in [StatusItem.PENDENTE, StatusItem.EM_ANDAMENTO]:
            self.status = StatusItem.ATRASADO
            self.save()

    def get_progresso(self):
        """Retorna o progresso das subtarefas (0-100)"""
        subtarefas = self.subtarefas.all()
        if not subtarefas:
            return 100 if self.status == StatusItem.CONCLUIDO else 0
        total = subtarefas.count()
        concluidas = subtarefas.filter(concluida=True).count()
        return int((concluidas / total) * 100) if total > 0 else 0


class SubTarefa(models.Model):
    """Subtarefa dentro de um item de checklist"""
    checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name='subtarefas')
    titulo = models.CharField(max_length=200)
    concluida = models.BooleanField(default=False)
    ordem = models.IntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Subtarefa'
        verbose_name_plural = 'Subtarefas'
        ordering = ['ordem', 'id']

    def __str__(self):
        status = '✓' if self.concluida else '○'
        return f"{status} {self.titulo}"


# ============================================
# PROJETOS (Sub-projetos de empresas)
# ============================================

class StatusProjeto(models.TextChoices):
    PLANEJAMENTO = 'planejamento', 'Planejamento'
    EM_ANDAMENTO = 'em_andamento', 'Em Andamento'
    EM_MANUTENCAO = 'em_manutencao', 'Em Manutenção'
    PAUSADO = 'pausado', 'Pausado'
    CONCLUIDO = 'concluido', 'Concluído'
    CANCELADO = 'cancelado', 'Cancelado'


class ProjetoTemplate(models.Model):
    """Template de projeto reutilizável"""
    titulo = models.CharField(max_length=300)
    descricao = models.TextField(blank=True)
    cor = models.CharField(max_length=7, default='#6366f1', help_text='Cor em hex')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Template de Projeto'
        verbose_name_plural = 'Templates de Projeto'
        ordering = ['titulo']

    def __str__(self):
        return self.titulo

    def get_total_etapas(self):
        return self.etapas.count()


class EtapaTemplate(models.Model):
    """Etapa dentro de um template de projeto"""
    template = models.ForeignKey(ProjetoTemplate, on_delete=models.CASCADE, related_name='etapas')
    titulo = models.CharField(max_length=300)
    descricao = models.TextField(blank=True)
    ordem = models.IntegerField(default=0)
    tempo_estimado = models.IntegerField(null=True, blank=True, help_text='Tempo estimado em minutos')

    class Meta:
        verbose_name = 'Etapa do Template'
        verbose_name_plural = 'Etapas do Template'
        ordering = ['ordem', 'id']

    def __str__(self):
        return f"{self.ordem}. {self.titulo}"


class Projeto(models.Model):
    """Sub-projeto dentro de uma empresa"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='projetos')
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='projetos')
    template_origem = models.ForeignKey(ProjetoTemplate, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='projetos_criados', help_text='Template usado para criar este projeto')
    titulo = models.CharField(max_length=300)
    descricao = models.TextField(blank=True)
    responsavel = models.ForeignKey(Pessoa, on_delete=models.SET_NULL, null=True, related_name='projetos_lider')
    prazo = models.DateField(null=True, blank=True, help_text='Prazo geral do projeto')
    status = models.CharField(max_length=20, choices=StatusProjeto.choices, default=StatusProjeto.PLANEJAMENTO)
    participantes = models.ManyToManyField(Pessoa, blank=True, related_name='projetos_participante')
    cor = models.CharField(max_length=7, default='#6366f1', help_text='Cor visual do projeto (hex)')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Projeto'
        verbose_name_plural = 'Projetos'
        ordering = ['-atualizado_em']

    def __str__(self):
        return f"{self.titulo} - {self.empresa.nome}"

    def get_progresso(self):
        """% baseado em demandas concluídas / total"""
        total = self.demandas.count()
        if total == 0:
            return 0
        concluidas = self.demandas.filter(status='concluido').count()
        return int((concluidas / total) * 100)

    @property
    def total_etapas(self):
        return self.demandas.count()

    @property
    def etapas_concluidas(self):
        return self.demandas.filter(status='concluido').count()

    def tempo_total(self):
        """Soma dos timers das demandas em segundos"""
        total = 0
        for d in self.demandas.all():
            total += d.get_tempo_total()
        return total

    def get_tempo_formatado(self):
        total = self.tempo_total()
        horas = total // 3600
        minutos = (total % 3600) // 60
        if horas > 0:
            return f"{horas}h {minutos}m"
        return f"{minutos}m"

    def esta_atrasado(self):
        if self.status == StatusProjeto.CONCLUIDO:
            return False
        if self.prazo and timezone.localdate() > self.prazo:
            return True
        return False


class TipoNoMapa(models.TextChoices):
    IDEIA = 'ideia', 'Ideia'
    NOTA = 'nota', 'Nota'
    RECURSO = 'recurso', 'Recurso'
    RISCO = 'risco', 'Risco'
    LINK = 'link', 'Link'


class MapaMentalNo(models.Model):
    """Nó extra do mapa mental (além das etapas)"""
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='nos_mapa')
    tipo = models.CharField(max_length=20, choices=TipoNoMapa.choices, default=TipoNoMapa.IDEIA)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    cor = models.CharField(max_length=7, default='#94a3b8', help_text='Cor do nó (hex)')
    url = models.URLField(blank=True, help_text='Link externo (opcional)')
    # Conexão: pode conectar a uma etapa ou ao projeto central
    conectado_a_etapa = models.ForeignKey('Demanda', on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='nos_conectados')
    posicao_x = models.IntegerField(default=0, help_text='Posição X no canvas')
    posicao_y = models.IntegerField(default=0, help_text='Posição Y no canvas')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Nó do Mapa Mental'
        verbose_name_plural = 'Nós do Mapa Mental'
        ordering = ['criado_em']

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.titulo}"


# ============================================
# DEMANDAS (Pendências com prazo)
# ============================================

class PrioridadeDemanda(models.TextChoices):
    BAIXA = 'baixa', 'Baixa'
    MEDIA = 'media', 'Média'
    ALTA = 'alta', 'Alta'
    URGENTE = 'urgente', 'Urgente'


class StatusDemanda(models.TextChoices):
    PENDENTE = 'pendente', 'Pendente'
    EM_ANDAMENTO = 'em_andamento', 'Em Andamento'
    DEPENDENTE = 'dependente', 'Aguardando Dependência'
    CONCLUIDO = 'concluido', 'Concluído'
    CANCELADO = 'cancelado', 'Cancelado'


class TipoEtapa(models.TextChoices):
    DESENVOLVIMENTO = 'desenvolvimento', 'Desenvolvimento'
    MELHORIA = 'melhoria', 'Melhoria'


class Demanda(models.Model):
    """Tarefa avulsa/pendência com prazo específico - criada por gestores"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='demandas')
    projeto = models.ForeignKey(Projeto, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='demandas', help_text='Projeto ao qual esta demanda pertence')
    etapa_ordem = models.IntegerField(default=0, help_text='Ordem da etapa dentro do projeto')
    tipo_etapa = models.CharField(max_length=20, choices=TipoEtapa.choices, default=TipoEtapa.DESENVOLVIMENTO,
                                   help_text='Tipo da etapa: desenvolvimento inicial ou melhoria')
    solicitante = models.ForeignKey(Pessoa, on_delete=models.SET_NULL, null=True, related_name='demandas_criadas',
                                     help_text='Gestor que criou a demanda')
    responsavel = models.ForeignKey(Pessoa, on_delete=models.SET_NULL, null=True, related_name='demandas_recebidas',
                                     help_text='Funcionário responsável por executar')

    # Conteúdo
    titulo = models.CharField(max_length=300)
    descricao = models.TextField(blank=True, help_text='Detalhes da demanda')
    instrucoes = models.TextField(blank=True, help_text='Instruções de como executar')

    # Prazo e tempo estimado
    prazo = models.DateTimeField(help_text='Data e hora limite para conclusão')
    prioridade = models.CharField(max_length=20, choices=PrioridadeDemanda.choices, default=PrioridadeDemanda.MEDIA)

    TEMPO_ESTIMADO_CHOICES = [
        (0, 'Não definido'),
        (15, '15 minutos'),
        (30, '30 minutos'),
        (45, '45 minutos'),
        (60, '1 hora'),
        (90, '1h30'),
        (120, '2 horas'),
        (180, '3 horas'),
        (240, '4 horas'),
        (480, '1 dia'),
        (960, '2 dias'),
        (1440, '3 dias'),
    ]
    tempo_estimado = models.IntegerField(default=0, choices=TEMPO_ESTIMADO_CHOICES,
                                          help_text='Tempo máximo estimado para conclusão')

    # Status
    status = models.CharField(max_length=20, choices=StatusDemanda.choices, default=StatusDemanda.PENDENTE)
    concluido_em = models.DateTimeField(null=True, blank=True)
    anotacoes = models.TextField(blank=True, help_text='Anotações do responsável durante execução')

    # Dependência
    dependente_de = models.ForeignKey(Pessoa, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='demandas_dependentes',
                                       help_text='Pessoa de quem esta demanda depende')
    dependente_externo = models.CharField(max_length=200, blank=True,
                                           help_text='Nome de pessoa externa (não cadastrada no sistema)')
    telefone_dependente_externo = models.CharField(max_length=20, blank=True,
                                                     help_text='WhatsApp da pessoa externa')
    motivo_dependencia = models.CharField(max_length=500, blank=True)
    dependencia_resolvida_em = models.DateTimeField(null=True, blank=True)

    # Timer de execução
    iniciado_em = models.DateTimeField(null=True, blank=True)
    timer_inicio = models.DateTimeField(null=True, blank=True)
    timer_acumulado = models.IntegerField(default=0, help_text='Tempo em segundos')
    timer_ativo = models.BooleanField(default=False)

    # Tracking
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Demanda'
        verbose_name_plural = 'Demandas'
        ordering = ['-prioridade', 'prazo', '-criado_em']

    def __str__(self):
        return f"{self.titulo} - {self.empresa.nome}"

    def esta_atrasada(self):
        """Verifica se a demanda está atrasada"""
        if self.status == StatusDemanda.CONCLUIDO:
            return False
        return timezone.now() > self.prazo

    def get_status_prazo(self):
        """Retorna status visual do prazo"""
        if self.status == StatusDemanda.CONCLUIDO:
            return 'concluido'
        now = timezone.now()
        if now > self.prazo:
            return 'atrasado'
        delta = self.prazo - now
        if delta.days <= 1:
            return 'urgente'
        if delta.days <= 3:
            return 'proximo'
        return 'normal'

    def iniciar_timer(self):
        """Inicia o timer"""
        if not self.timer_ativo:
            agora = timezone.now()
            self.timer_inicio = agora
            self.timer_ativo = True
            if not self.iniciado_em:
                self.iniciado_em = agora
            if self.status == StatusDemanda.PENDENTE:
                self.status = StatusDemanda.EM_ANDAMENTO
            self.save()

    def pausar_timer(self):
        """Pausa o timer"""
        if self.timer_ativo and self.timer_inicio:
            delta = timezone.now() - self.timer_inicio
            self.timer_acumulado += int(delta.total_seconds())
            self.timer_ativo = False
            self.timer_inicio = None
            self.save()

    def get_tempo_total(self):
        """Tempo total em segundos"""
        total = self.timer_acumulado
        if self.timer_ativo and self.timer_inicio:
            delta = timezone.now() - self.timer_inicio
            total += int(delta.total_seconds())
        return total

    def get_tempo_formatado(self):
        """Tempo formatado HH:MM:SS"""
        total = self.get_tempo_total()
        horas = total // 3600
        minutos = (total % 3600) // 60
        segundos = total % 60
        if horas > 0:
            return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        return f"{minutos:02d}:{segundos:02d}"

    def marcar_concluido(self):
        """Marca como concluído"""
        self.pausar_timer()
        self.status = StatusDemanda.CONCLUIDO
        self.concluido_em = timezone.now()
        self.save()

    def reabrir(self):
        """Reabre a demanda"""
        self.status = StatusDemanda.EM_ANDAMENTO
        self.concluido_em = None
        self.save()

    def get_progresso(self):
        """Retorna progresso das subtarefas (0-100)"""
        subtarefas = self.subtarefas_demanda.all()
        if not subtarefas:
            return 100 if self.status == StatusDemanda.CONCLUIDO else 0
        total = subtarefas.count()
        concluidas = subtarefas.filter(concluida=True).count()
        return int((concluidas / total) * 100) if total > 0 else 0


class SubTarefaDemanda(models.Model):
    """Subtarefa dentro de uma demanda"""
    demanda = models.ForeignKey(Demanda, on_delete=models.CASCADE, related_name='subtarefas_demanda')
    titulo = models.CharField(max_length=200)
    concluida = models.BooleanField(default=False)
    ordem = models.IntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Subtarefa de Demanda'
        verbose_name_plural = 'Subtarefas de Demanda'
        ordering = ['ordem', 'id']

    def __str__(self):
        status = '✓' if self.concluida else '○'
        return f"{status} {self.titulo}"


class AnexoDemanda(models.Model):
    """Arquivo anexado a uma demanda"""
    demanda = models.ForeignKey(Demanda, on_delete=models.CASCADE, related_name='anexos')
    arquivo = models.FileField(upload_to='demandas/anexos/%Y/%m/')
    nome_original = models.CharField(max_length=255)
    tamanho = models.IntegerField(default=0, help_text='Tamanho em bytes')
    enviado_por = models.ForeignKey(Pessoa, on_delete=models.SET_NULL, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome_original

    def get_tamanho_formatado(self):
        """Retorna tamanho formatado (KB, MB)"""
        if self.tamanho < 1024:
            return f"{self.tamanho} B"
        elif self.tamanho < 1024 * 1024:
            return f"{self.tamanho / 1024:.1f} KB"
        else:
            return f"{self.tamanho / (1024 * 1024):.1f} MB"


class ComentarioDemanda(models.Model):
    """Comentário/atualização em uma demanda"""
    demanda = models.ForeignKey(Demanda, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(Pessoa, on_delete=models.SET_NULL, null=True)
    texto = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comentário'
        verbose_name_plural = 'Comentários'
        ordering = ['criado_em']

    def __str__(self):
        return f"{self.autor.nome}: {self.texto[:50]}..."


# ============================================
# APROVEITAMENTO DIÁRIO
# ============================================

class AproveitamentoDiario(models.Model):
    """Registro do aproveitamento diário de cada pessoa"""
    pessoa = models.ForeignKey(Pessoa, on_delete=models.CASCADE, related_name='aproveitamentos')
    data = models.DateField()

    # Métricas
    total_tarefas = models.IntegerField(default=0)
    tarefas_concluidas = models.IntegerField(default=0)
    tarefas_nao_concluidas = models.IntegerField(default=0)
    percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Tempo trabalhado
    tempo_total_segundos = models.IntegerField(default=0, help_text='Tempo total trabalhado em segundos')

    # Tracking
    fechado_em = models.DateTimeField(null=True, blank=True, help_text='Quando o dia foi fechado')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Aproveitamento Diário'
        verbose_name_plural = 'Aproveitamentos Diários'
        ordering = ['-data']
        unique_together = ['pessoa', 'data']

    def __str__(self):
        return f"{self.pessoa.nome} - {self.data} - {self.percentual}%"

    def get_tempo_formatado(self):
        """Tempo formatado HH:MM"""
        horas = self.tempo_total_segundos // 3600
        minutos = (self.tempo_total_segundos % 3600) // 60
        return f"{horas:02d}:{minutos:02d}"

    @classmethod
    def calcular_para_pessoa(cls, pessoa, data):
        """Calcula e salva o aproveitamento de uma pessoa em uma data"""
        items = ChecklistItem.objects.filter(
            responsavel=pessoa,
            data_referencia=data
        )

        total = items.count()
        concluidos = items.filter(status=StatusItem.CONCLUIDO).count()
        nao_concluidos = total - concluidos
        percentual = (concluidos / total * 100) if total > 0 else 0
        tempo_total = sum(item.get_tempo_total() for item in items)

        aproveitamento, created = cls.objects.update_or_create(
            pessoa=pessoa,
            data=data,
            defaults={
                'total_tarefas': total,
                'tarefas_concluidas': concluidos,
                'tarefas_nao_concluidas': nao_concluidos,
                'percentual': percentual,
                'tempo_total_segundos': tempo_total,
            }
        )
        return aproveitamento


class TarefaNaoConcluida(models.Model):
    """Registro de tarefa não concluída com justificativa"""
    checklist_item = models.OneToOneField(ChecklistItem, on_delete=models.CASCADE, related_name='registro_nao_concluida')
    aproveitamento = models.ForeignKey(AproveitamentoDiario, on_delete=models.CASCADE, related_name='tarefas_nao_concluidas_detalhe')

    justificativa = models.TextField(help_text='Motivo por não ter concluído')
    registrado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tarefa Não Concluída'
        verbose_name_plural = 'Tarefas Não Concluídas'

    def __str__(self):
        return f"{self.checklist_item.template.titulo} - {self.checklist_item.data_referencia}"
