from django.db import models
from django.utils import timezone
from core.models import Empresa, Pessoa
from checklists.models import Projeto


class MetaEmpresa(models.Model):
    """Meta financeira mensal de uma empresa"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='metas')
    mes = models.IntegerField(help_text='Mês (1-12)')
    ano = models.IntegerField(help_text='Ano')
    valor_meta = models.DecimalField(max_digits=12, decimal_places=2, help_text='Meta mensal em R$')
    dias_uteis = models.IntegerField(default=22, help_text='Dias úteis no mês')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Meta'
        verbose_name_plural = 'Metas'
        unique_together = ['empresa', 'mes', 'ano']
        ordering = ['-ano', '-mes']

    def __str__(self):
        return f"{self.empresa.nome} - {self.mes:02d}/{self.ano} - R$ {self.valor_meta:,.2f}"

    @property
    def meta_diaria(self):
        if self.dias_uteis > 0:
            return self.valor_meta / self.dias_uteis
        return self.valor_meta

    def get_realizado_mes(self):
        lancamentos = Lancamento.objects.filter(
            empresa=self.empresa, data__month=self.mes, data__year=self.ano,
        )
        entradas = lancamentos.filter(tipo='entrada').aggregate(
            total=models.Sum('valor'))['total'] or 0
        saidas = lancamentos.filter(tipo='saida').aggregate(
            total=models.Sum('valor'))['total'] or 0
        return entradas - saidas

    def get_entradas_mes(self):
        return Lancamento.objects.filter(
            empresa=self.empresa, data__month=self.mes, data__year=self.ano, tipo='entrada'
        ).aggregate(total=models.Sum('valor'))['total'] or 0

    def get_saidas_mes(self):
        return Lancamento.objects.filter(
            empresa=self.empresa, data__month=self.mes, data__year=self.ano, tipo='saida'
        ).aggregate(total=models.Sum('valor'))['total'] or 0

    def get_progresso(self):
        realizado = self.get_realizado_mes()
        if self.valor_meta > 0:
            return min(int((realizado / self.valor_meta) * 100), 999)
        return 0

    def get_realizado_dia(self, data=None):
        if data is None:
            data = timezone.localdate()
        lancamentos = Lancamento.objects.filter(empresa=self.empresa, data=data)
        entradas = lancamentos.filter(tipo='entrada').aggregate(
            total=models.Sum('valor'))['total'] or 0
        saidas = lancamentos.filter(tipo='saida').aggregate(
            total=models.Sum('valor'))['total'] or 0
        return entradas - saidas

    def get_dias_passados(self):
        hoje = timezone.localdate()
        if hoje.month != self.mes or hoje.year != self.ano:
            return self.dias_uteis
        from datetime import date
        dias = 0
        for dia in range(1, hoje.day + 1):
            d = date(self.ano, self.mes, dia)
            if d.weekday() < 6:
                dias += 1
        return dias

    def get_dias_restantes(self):
        hoje = timezone.localdate()
        if hoje.month != self.mes or hoje.year != self.ano:
            return 0
        import calendar
        from datetime import date
        ultimo_dia = calendar.monthrange(self.ano, self.mes)[1]
        restantes = 0
        for dia in range(hoje.day + 1, ultimo_dia + 1):
            d = date(self.ano, self.mes, dia)
            if d.weekday() < 6:
                restantes += 1
        return restantes

    def get_meta_diaria_restante(self):
        falta = float(self.valor_meta) - float(self.get_realizado_mes())
        dias = self.get_dias_restantes()
        if dias > 0 and falta > 0:
            return falta / dias
        return 0

    def get_projecao_mes(self):
        dias_passados = self.get_dias_passados()
        if dias_passados > 0:
            media_diaria = float(self.get_realizado_mes()) / dias_passados
            return media_diaria * self.dias_uteis
        return 0

    def bateu_meta(self):
        return self.get_realizado_mes() >= self.valor_meta


class TipoLancamento(models.TextChoices):
    ENTRADA = 'entrada', 'Entrada'
    SAIDA = 'saida', 'Saída'


class ContaBancaria(models.Model):
    """Conta bancária vinculada a uma empresa"""
    TIPO_CONTA_CHOICES = [
        ('corrente', 'Conta Corrente'),
        ('poupanca', 'Poupança'),
        ('pagamento', 'Conta de Pagamento'),
        ('investimento', 'Investimento'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='contas_bancarias')
    nome = models.CharField(max_length=100, help_text='Ex: Bradesco PJ, Nubank, Inter')
    banco = models.CharField(max_length=100, blank=True, help_text='Nome do banco')
    tipo_conta = models.CharField(max_length=20, choices=TIPO_CONTA_CHOICES, default='corrente')
    agencia = models.CharField(max_length=20, blank=True)
    numero_conta = models.CharField(max_length=30, blank=True)
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                         help_text='Saldo no momento do cadastro')
    cor = models.CharField(max_length=7, default='#3b82f6', help_text='Cor para identificação')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Conta Bancária'
        verbose_name_plural = 'Contas Bancárias'
        ordering = ['empresa', 'nome']

    def __str__(self):
        return f"{self.nome} - {self.empresa.nome}"

    def get_saldo(self):
        """Saldo atual = saldo_inicial + entradas - saídas desta conta"""
        from django.db.models import Sum
        lancamentos = Lancamento.objects.filter(conta=self)
        entradas = lancamentos.filter(tipo='entrada').aggregate(t=Sum('valor'))['t'] or 0
        saidas = lancamentos.filter(tipo='saida').aggregate(t=Sum('valor'))['t'] or 0
        return self.saldo_inicial + entradas - saidas


class CategoriaLancamento(models.Model):
    """Categoria customizável (global ou por empresa)"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='categorias_financeiro',
                                null=True, blank=True, help_text='Vazio = categoria global')
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TipoLancamento.choices)
    cor = models.CharField(max_length=7, default='#6b7280')
    ativo = models.BooleanField(default=True)
    ordem = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['tipo', 'ordem', 'nome']

    def __str__(self):
        prefixo = f"[{self.empresa.nome}] " if self.empresa else ""
        return f"{prefixo}{self.get_tipo_display()} - {self.nome}"


class Lancamento(models.Model):
    """Lançamento financeiro diário"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='lancamentos')
    conta = models.ForeignKey(ContaBancaria, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='lancamentos', help_text='Conta bancária relacionada')
    projeto = models.ForeignKey(Projeto, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='lancamentos')
    tipo = models.CharField(max_length=10, choices=TipoLancamento.choices)
    categoria = models.ForeignKey(CategoriaLancamento, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='lancamentos')
    descricao = models.CharField(max_length=300)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data = models.DateField(default=timezone.localdate)
    pessoa = models.ForeignKey(Pessoa, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='lancamentos', help_text='Pessoa relacionada')
    observacao = models.TextField(blank=True)
    mp_payment_id = models.CharField(max_length=50, null=True, blank=True, unique=True,
                                      help_text='ID do pagamento Mercado Pago (evita duplicação)')
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(Pessoa, on_delete=models.SET_NULL, null=True,
                                    related_name='lancamentos_criados')

    class Meta:
        verbose_name = 'Lançamento'
        verbose_name_plural = 'Lançamentos'
        ordering = ['-data', '-criado_em']

    def __str__(self):
        sinal = '+' if self.tipo == 'entrada' else '-'
        return f"{self.data} | {sinal} R$ {self.valor:,.2f} | {self.descricao}"

    @property
    def total_prestacoes(self):
        """Total de gastos empresariais vinculados a esta retirada."""
        return self.prestacoes.aggregate(t=models.Sum('valor'))['t'] or 0

    @property
    def retirada_liquida(self):
        """Valor real da retirada pessoal (valor - prestações de conta)."""
        return self.valor - self.total_prestacoes


class PrestacaoConta(models.Model):
    """
    Detalha gastos empresariais pagos com dinheiro de uma retirada.
    Não afeta o saldo da conta (é apenas informativo).
    Ex: Renan retirou R$1000, pagou R$300 de marketing → retirada líquida = R$700.
    """
    lancamento = models.ForeignKey(Lancamento, on_delete=models.CASCADE, related_name='prestacoes',
                                    help_text='Lançamento de retirada original')
    descricao = models.CharField(max_length=300, help_text='Ex: Marketing Facebook, Frete correios')
    categoria = models.ForeignKey(CategoriaLancamento, on_delete=models.SET_NULL, null=True, blank=True)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Prestação de Conta'
        verbose_name_plural = 'Prestações de Conta'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.descricao} - R$ {self.valor:,.2f}"


class ContaPagar(models.Model):
    """Template de conta a pagar (recorrente, única ou parcelada)"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='contas_pagar')
    descricao = models.CharField(max_length=300, help_text='Ex: Internet Vivo, Aluguel')
    valor = models.DecimalField(max_digits=12, decimal_places=2, help_text='Valor total (ou da parcela se parcelado)')
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                       help_text='Valor total da compra (quando parcelado)')
    categoria = models.ForeignKey(CategoriaLancamento, on_delete=models.SET_NULL, null=True, blank=True)
    conta = models.ForeignKey(ContaBancaria, on_delete=models.SET_NULL, null=True, blank=True)

    # Parcelamento
    parcelado = models.BooleanField(default=False, help_text='Se é uma compra parcelada')
    total_parcelas = models.IntegerField(default=1, help_text='Número total de parcelas')

    RECORRENCIA_CHOICES = [
        ('unica', 'Única (sem recorrência)'),
        ('parcelada', 'Parcelada'),
        ('diaria', 'Diária'),
        ('semanal', 'Semanal'),
        ('quinzenal', 'Quinzenal'),
        ('mensal', 'Mensal'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
    ]
    recorrencia = models.CharField(max_length=12, choices=RECORRENCIA_CHOICES, default='mensal')
    data_vencimento = models.DateField(null=True, blank=True, help_text='Data do primeiro vencimento')
    # Campo legado - mantido para compatibilidade, extraído automaticamente de data_vencimento
    dia_vencimento = models.IntegerField(default=1, help_text='Dia do mês que vence (1-31)')

    DIA_EXECUCAO_CHOICES = [
        ('mesmo_dia', 'No dia do vencimento'),
        ('dia_mes', 'Dia específico do mês'),
        ('segunda', 'Toda Segunda'),
        ('terca', 'Toda Terça'),
        ('quarta', 'Toda Quarta'),
        ('quinta', 'Toda Quinta'),
        ('sexta', 'Toda Sexta'),
        ('sabado', 'Todo Sábado'),
    ]
    dia_execucao = models.CharField(max_length=10, choices=DIA_EXECUCAO_CHOICES, default='mesmo_dia')
    dia_execucao_mensal = models.IntegerField(null=True, blank=True, help_text='Dia do mês para execução (1-31)')

    ativo = models.BooleanField(default=True)
    observacao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Conta a Pagar'
        verbose_name_plural = 'Contas a Pagar'
        ordering = ['empresa', 'descricao']

    def __str__(self):
        return f"{self.descricao} - R$ {self.valor:,.2f} ({self.get_recorrencia_display()})"


class ContaPagarItem(models.Model):
    """Instância mensal de uma conta a pagar ou parcela"""
    conta_pagar = models.ForeignKey(ContaPagar, on_delete=models.CASCADE, related_name='itens')
    mes = models.IntegerField()
    ano = models.IntegerField()
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data_vencimento = models.DateField()
    data_execucao = models.DateField(help_text='Dia que deve aparecer na rotina')
    pago = models.BooleanField(default=False)
    pago_em = models.DateTimeField(null=True, blank=True)
    lancamento = models.ForeignKey(Lancamento, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='conta_pagar_item')
    # Para contas parceladas
    parcela_numero = models.IntegerField(null=True, blank=True, help_text='Número da parcela (1, 2, 3...)')

    class Meta:
        verbose_name = 'Item Conta a Pagar'
        verbose_name_plural = 'Itens Contas a Pagar'
        ordering = ['data_vencimento']

    def __str__(self):
        status = 'Pago' if self.pago else 'Pendente'
        if self.parcela_numero and self.conta_pagar.total_parcelas > 1:
            return f"{self.conta_pagar.descricao} - Parcela {self.parcela_numero}/{self.conta_pagar.total_parcelas} - {status}"
        return f"{self.conta_pagar.descricao} - {self.mes:02d}/{self.ano} - {status}"


class ConfigMercadoPago(models.Model):
    """Configuração de integração Mercado Pago por empresa"""
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name='config_mp')
    access_token = models.CharField(max_length=200, help_text='Access Token do Mercado Pago')
    ativo = models.BooleanField(default=True)
    ultima_sync = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Config Mercado Pago'
        verbose_name_plural = 'Configs Mercado Pago'

    def __str__(self):
        return f"MP - {self.empresa.nome} ({'Ativo' if self.ativo else 'Inativo'})"


class ContaReceber(models.Model):
    """Template de conta a receber (recorrente, única ou parcelada)"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='contas_receber')
    cliente = models.ForeignKey(Pessoa, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='contas_receber', help_text='Cliente devedor')
    projeto = models.ForeignKey(Projeto, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='contas_receber', help_text='Projeto relacionado')
    descricao = models.CharField(max_length=300, help_text='Ex: Mensalidade, Projeto X, Consultoria')
    valor = models.DecimalField(max_digits=12, decimal_places=2, help_text='Valor total (ou da parcela se parcelado)')
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                       help_text='Valor total do contrato (quando parcelado)')
    categoria = models.ForeignKey(CategoriaLancamento, on_delete=models.SET_NULL, null=True, blank=True)
    conta = models.ForeignKey(ContaBancaria, on_delete=models.SET_NULL, null=True, blank=True,
                               help_text='Conta onde será recebido')

    # Parcelamento
    parcelado = models.BooleanField(default=False, help_text='Se é um recebimento parcelado')
    total_parcelas = models.IntegerField(default=1, help_text='Número total de parcelas')

    RECORRENCIA_CHOICES = [
        ('unica', 'Única (sem recorrência)'),
        ('parcelada', 'Parcelada'),
        ('semanal', 'Semanal'),
        ('quinzenal', 'Quinzenal'),
        ('mensal', 'Mensal'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
    ]
    recorrencia = models.CharField(max_length=12, choices=RECORRENCIA_CHOICES, default='mensal')
    data_vencimento = models.DateField(null=True, blank=True, help_text='Data do primeiro vencimento')
    dia_vencimento = models.IntegerField(default=1, help_text='Dia do mês que vence (1-31)')

    # Notificações
    notificar_cliente = models.BooleanField(default=False, help_text='Enviar lembrete ao cliente')
    dias_antecedencia = models.IntegerField(default=3, help_text='Dias antes do vencimento para notificar')

    ativo = models.BooleanField(default=True)
    observacao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Conta a Receber'
        verbose_name_plural = 'Contas a Receber'
        ordering = ['empresa', 'descricao']

    def __str__(self):
        cliente_nome = f" - {self.cliente.nome}" if self.cliente else ""
        return f"{self.descricao}{cliente_nome} - R$ {self.valor:,.2f} ({self.get_recorrencia_display()})"

    def get_total_recebido(self):
        """Total já recebido desta conta"""
        return self.itens.filter(recebido=True).aggregate(t=models.Sum('valor'))['t'] or 0

    def get_total_pendente(self):
        """Total ainda pendente"""
        return self.itens.filter(recebido=False).aggregate(t=models.Sum('valor'))['t'] or 0

    def get_total_atrasado(self):
        """Total em atraso"""
        hoje = timezone.localdate()
        return self.itens.filter(recebido=False, data_vencimento__lt=hoje).aggregate(t=models.Sum('valor'))['t'] or 0


class ContaReceberItem(models.Model):
    """Instância mensal/parcela de uma conta a receber"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('recebido', 'Recebido'),
        ('atrasado', 'Atrasado'),
        ('cancelado', 'Cancelado'),
    ]

    conta_receber = models.ForeignKey(ContaReceber, on_delete=models.CASCADE, related_name='itens')
    mes = models.IntegerField()
    ano = models.IntegerField()
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data_vencimento = models.DateField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pendente')
    recebido = models.BooleanField(default=False)
    recebido_em = models.DateTimeField(null=True, blank=True)
    valor_recebido = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                          help_text='Valor efetivamente recebido (pode ser diferente do esperado)')
    lancamento = models.ForeignKey(Lancamento, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='conta_receber_item')
    # Para contas parceladas
    parcela_numero = models.IntegerField(null=True, blank=True, help_text='Número da parcela (1, 2, 3...)')
    # Notificação
    notificado = models.BooleanField(default=False)
    notificado_em = models.DateTimeField(null=True, blank=True)
    observacao = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Item Conta a Receber'
        verbose_name_plural = 'Itens Contas a Receber'
        ordering = ['data_vencimento']

    def __str__(self):
        if self.parcela_numero and self.conta_receber.total_parcelas > 1:
            return f"{self.conta_receber.descricao} - Parcela {self.parcela_numero}/{self.conta_receber.total_parcelas} - {self.get_status_display()}"
        return f"{self.conta_receber.descricao} - {self.mes:02d}/{self.ano} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Atualiza status automaticamente
        if self.recebido:
            self.status = 'recebido'
        elif self.status != 'cancelado':
            hoje = timezone.localdate()
            if self.data_vencimento < hoje:
                self.status = 'atrasado'
            else:
                self.status = 'pendente'
        super().save(*args, **kwargs)

    @property
    def esta_atrasado(self):
        if self.recebido:
            return False
        return self.data_vencimento < timezone.localdate()

    @property
    def dias_atraso(self):
        if not self.esta_atrasado:
            return 0
        return (timezone.localdate() - self.data_vencimento).days


class AlertaFinanceiro(models.Model):
    """Configuracao de alertas financeiros automaticos"""
    TIPO_ALERTA_CHOICES = [
        ('conta_pagar_vencendo', 'Conta a Pagar Vencendo'),
        ('conta_pagar_atrasada', 'Conta a Pagar Atrasada'),
        ('conta_receber_vencendo', 'Conta a Receber Vencendo'),
        ('conta_receber_atrasada', 'Conta a Receber Atrasada'),
        ('meta_diaria', 'Meta Diaria Nao Atingida'),
        ('saldo_baixo', 'Saldo Baixo em Conta'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='alertas_financeiros')
    tipo = models.CharField(max_length=30, choices=TIPO_ALERTA_CHOICES)
    ativo = models.BooleanField(default=True)
    dias_antecedencia = models.IntegerField(default=3, help_text='Dias antes do vencimento para alertar')
    valor_limite = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                        help_text='Valor limite para alerta de saldo baixo')
    notificar_whatsapp = models.BooleanField(default=True)
    destinatarios = models.ManyToManyField(Pessoa, blank=True, related_name='alertas_financeiros',
                                            help_text='Pessoas que receberao o alerta')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Alerta Financeiro'
        verbose_name_plural = 'Alertas Financeiros'
        ordering = ['empresa', 'tipo']

    def __str__(self):
        return f"{self.empresa.nome} - {self.get_tipo_display()}"


class HistoricoAlerta(models.Model):
    """Historico de alertas enviados"""
    alerta = models.ForeignKey(AlertaFinanceiro, on_delete=models.CASCADE, related_name='historico')
    mensagem = models.TextField()
    enviado_em = models.DateTimeField(auto_now_add=True)
    enviado_para = models.ManyToManyField(Pessoa, blank=True, related_name='alertas_recebidos')
    sucesso = models.BooleanField(default=True)
    erro = models.TextField(blank=True)
    # Referencia ao objeto que gerou o alerta
    conta_pagar_item = models.ForeignKey(ContaPagarItem, on_delete=models.SET_NULL, null=True, blank=True)
    conta_receber_item = models.ForeignKey(ContaReceberItem, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Historico de Alerta'
        verbose_name_plural = 'Historico de Alertas'
        ordering = ['-enviado_em']

    def __str__(self):
        return f"{self.alerta.get_tipo_display()} - {self.enviado_em.strftime('%d/%m/%Y %H:%M')}"
