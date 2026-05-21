"""
Scheduler leve - roda em loop e executa os agendamentos configurados.
Uso: python manage.py scheduler

Verifica a cada 60 segundos se há agendamentos pendentes.
Gera tarefas recorrentes automaticamente à meia-noite.
"""
import time
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone


class Command(BaseCommand):
    help = 'Scheduler de notificações e tarefas automáticas'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Scheduler iniciado. Verificando a cada 60s...'))
        self._ultimo_dia_gerado = None

        # Gerar tarefas do dia ao iniciar
        self.gerar_tarefas_se_necessario()

        while True:
            try:
                self.verificar_agendamentos()
                self.gerar_tarefas_se_necessario()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro: {e}'))
            time.sleep(60)

    def gerar_tarefas_se_necessario(self):
        """Gera tarefas recorrentes do dia"""
        hoje = timezone.localdate()

        if self._ultimo_dia_gerado == hoje:
            return

        self.stdout.write(f'[{timezone.localtime().strftime("%H:%M")}] Gerando tarefas para {hoje}...')
        try:
            call_command('gerar_tarefas_dia')
            call_command('gerar_checklists', '--atualizar-atrasados')

            from financeiro.services import gerar_contas_pagar_todas_empresas
            criados = gerar_contas_pagar_todas_empresas()
            if criados:
                self.stdout.write(f'  {criados} conta(s) a pagar gerada(s).')

            self._ultimo_dia_gerado = hoje
            self.stdout.write(self.style.SUCCESS(f'  Tarefas do dia {hoje} geradas.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Erro: {e}'))

    def verificar_agendamentos(self):
        agora = timezone.localtime()

        try:
            from notifications.models import AgendamentoNotificacao

            for agendamento in AgendamentoNotificacao.objects.filter(ativo=True):
                if agendamento.deve_executar_hoje(agora):
                    self.stdout.write(f'[{agora.strftime("%H:%M")}] Executando: {agendamento.get_tipo_display()}')
                    self.executar(agendamento)
                    agendamento.ultima_execucao = timezone.now()
                    agendamento.save()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Erro agendamentos: {e}'))

    def executar(self, agendamento):
        from notifications.wapi import (
            processar_lembretes_diarios,
            processar_cobrancas,
            processar_cobrancas_externas,
            processar_resumo_dependencias,
        )

        tipo = agendamento.tipo

        if tipo == 'lembrete_diario':
            resultado = processar_lembretes_diarios()
            self.stdout.write(f'  Lembretes: {resultado["enviados"]} enviados, {resultado["erros"]} erros')

        elif tipo == 'cobranca_funcionarios':
            resultado = processar_cobrancas()
            self.stdout.write(f'  Cobranças funcionários: {resultado["enviados"]} enviados, {resultado["erros"]} erros')

        elif tipo == 'resumo_dependencias':
            resultado = processar_resumo_dependencias()
            self.stdout.write(f'  Resumo dependências: {resultado["enviados"]} enviados, {resultado["erros"]} erros')

        elif tipo == 'cobranca_externos':
            resultado = processar_cobrancas_externas()
            self.stdout.write(f'  Cobranças externas: {resultado["enviados"]} enviados, {resultado["erros"]} erros')
