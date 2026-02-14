"""
Scheduler leve - roda em loop e executa os agendamentos configurados.
Uso: python manage.py scheduler

Verifica a cada 60 segundos se há agendamentos pendentes.
Gera tarefas recorrentes automaticamente à meia-noite.
Multi-tenant: itera sobre todos os tenants ativos.
"""
import time
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from django_tenants.utils import tenant_context
from tenants.models import Client


class Command(BaseCommand):
    help = 'Scheduler de notificações e tarefas automáticas (multi-tenant)'

    def _get_tenants(self):
        """Retorna todos os tenants ativos (exceto public)"""
        return Client.objects.exclude(schema_name='public').filter(ativo=True)

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Scheduler iniciado (multi-tenant). Verificando a cada 60s...'))
        self._ultimo_dia_gerado = {}

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
        """Gera tarefas recorrentes do dia para cada tenant"""
        hoje = timezone.localdate()

        for tenant in self._get_tenants():
            if self._ultimo_dia_gerado.get(tenant.schema_name) == hoje:
                continue

            self.stdout.write(f'[{timezone.localtime().strftime("%H:%M")}] [{tenant.nome}] Gerando tarefas para {hoje}...')
            try:
                with tenant_context(tenant):
                    call_command('gerar_tarefas_dia')
                    call_command('gerar_checklists', '--atualizar-atrasados')

                    from financeiro.services import gerar_contas_pagar_todas_empresas
                    criados = gerar_contas_pagar_todas_empresas()
                    if criados:
                        self.stdout.write(f'  [{tenant.nome}] {criados} conta(s) a pagar gerada(s).')

                self._ultimo_dia_gerado[tenant.schema_name] = hoje
                self.stdout.write(self.style.SUCCESS(f'  [{tenant.nome}] Tarefas do dia {hoje} geradas.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [{tenant.nome}] Erro: {e}'))

    def verificar_agendamentos(self):
        agora = timezone.localtime()

        for tenant in self._get_tenants():
            try:
                with tenant_context(tenant):
                    from notifications.models import AgendamentoNotificacao

                    for agendamento in AgendamentoNotificacao.objects.filter(ativo=True):
                        if agendamento.deve_executar_hoje(agora):
                            self.stdout.write(f'[{agora.strftime("%H:%M")}] [{tenant.nome}] Executando: {agendamento.get_tipo_display()}')
                            self.executar(agendamento)
                            agendamento.ultima_execucao = timezone.now()
                            agendamento.save()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [{tenant.nome}] Erro agendamentos: {e}'))

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
