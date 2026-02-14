from django.db import models
from core.models import Pessoa
from checklists.models import ChecklistItem


class TipoNotificacao(models.TextChoices):
    LEMBRETE = 'lembrete', 'Lembrete'
    COBRANCA = 'cobranca', 'Cobrança'
    CONFIRMACAO = 'confirmacao', 'Confirmação'


class DiaSemana(models.TextChoices):
    SEG = 'seg', 'Segunda'
    TER = 'ter', 'Terça'
    QUA = 'qua', 'Quarta'
    QUI = 'qui', 'Quinta'
    SEX = 'sex', 'Sexta'
    SAB = 'sab', 'Sábado'
    DOM = 'dom', 'Domingo'


DIA_SEMANA_MAP = {
    0: 'seg', 1: 'ter', 2: 'qua', 3: 'qui', 4: 'sex', 5: 'sab', 6: 'dom'
}


class AgendamentoNotificacao(models.Model):
    """Configuração de agendamento de notificações automáticas"""

    class TipoAgendamento(models.TextChoices):
        LEMBRETE_DIARIO = 'lembrete_diario', 'Lembrete Diário (funcionários)'
        COBRANCA_FUNCIONARIOS = 'cobranca_funcionarios', 'Cobrança Funcionários'
        COBRANCA_EXTERNOS = 'cobranca_externos', 'Cobrança Pessoas Externas'
        RESUMO_DEPENDENCIAS = 'resumo_dependencias', 'Resumo das Minhas Dependências'

    class Recorrencia(models.TextChoices):
        DIARIO = 'diario', 'Diário (dias da semana)'
        SEMANAL = 'semanal', 'Semanal (um dia fixo)'
        MENSAL = 'mensal', 'Mensal (dia do mês)'

    tipo = models.CharField(max_length=30, choices=TipoAgendamento.choices)
    nome = models.CharField(max_length=100, blank=True, help_text='Rótulo opcional (ex: Lembrete Manhã, Lembrete Tarde)')
    ativo = models.BooleanField(default=True)
    recorrencia = models.CharField(max_length=10, choices=Recorrencia.choices, default='diario')
    horario = models.TimeField(default='09:00', help_text='Horário de envio')
    dias_semana = models.CharField(
        max_length=50, default='seg,ter,qua,qui,sex',
        help_text='Dias separados por vírgula: seg,ter,qua,qui,sex,sab,dom'
    )
    dia_mes = models.IntegerField(
        null=True, blank=True,
        help_text='Dia do mês para recorrência mensal (1-31)'
    )
    ultima_execucao = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Agendamento de Notificação'
        verbose_name_plural = 'Agendamentos de Notificações'

    def __str__(self):
        status = '✓' if self.ativo else '✗'
        label = self.nome or self.get_tipo_display()
        if self.recorrencia == 'mensal' and self.dia_mes:
            quando = f'dia {self.dia_mes} do mês'
        elif self.recorrencia == 'semanal':
            quando = self.dias_semana
        else:
            quando = self.dias_semana
        return f"{status} {label} - {self.horario} ({quando})"

    def dias_lista(self):
        return [d.strip() for d in self.dias_semana.split(',') if d.strip()]

    def deve_executar_hoje(self, agora=None):
        """Verifica se deve executar hoje baseado na recorrência e horário"""
        from django.utils import timezone
        if not agora:
            agora = timezone.localtime()

        # Já executou hoje?
        if self.ultima_execucao:
            ultima_local = timezone.localtime(self.ultima_execucao)
            if ultima_local.date() == agora.date():
                return False

        # Verificar recorrência
        if self.recorrencia == 'mensal':
            if self.dia_mes and agora.day != self.dia_mes:
                return False
        else:
            # diario e semanal usam dias_semana
            dia_atual = DIA_SEMANA_MAP.get(agora.weekday())
            if dia_atual not in self.dias_lista():
                return False

        # Passou do horário?
        return agora.time() >= self.horario


class NotificacaoWhatsApp(models.Model):
    """Log de notificações enviadas via WhatsApp"""
    pessoa = models.ForeignKey(Pessoa, on_delete=models.CASCADE, related_name='notificacoes')
    checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE,
                                        null=True, blank=True, related_name='notificacoes')
    tipo = models.CharField(max_length=20, choices=TipoNotificacao.choices)
    mensagem = models.TextField()
    telefone = models.CharField(max_length=20)

    # Status do envio
    enviado = models.BooleanField(default=False)
    enviado_em = models.DateTimeField(null=True, blank=True)
    erro = models.TextField(blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificação WhatsApp'
        verbose_name_plural = 'Notificações WhatsApp'
        ordering = ['-criado_em']

    def __str__(self):
        status = '✓' if self.enviado else '✗'
        return f"{status} {self.tipo} - {self.pessoa.nome}"
