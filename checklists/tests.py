"""
Testes do NeuraxoCheck - Checklists, Demandas, Rotinas
"""
from django.test import TestCase, Client as TestClient
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from core.models import Empresa, Pessoa, PapelEmpresa, NotificacaoInApp
from checklists.models import (
    ChecklistTemplate, ChecklistItem, SubTarefaTemplate, SubTarefa,
    Demanda, Projeto,
)


class BaseTestCase(TestCase):
    def setUp(self):
        self.neuraxo = Empresa.objects.create(nome='Neuraxo')
        self.rw6 = Empresa.objects.create(nome='RW6')

        self.user_gestor = User.objects.create_user('gestor', 'gestor@test.com', 'pass123')
        self.user_func = User.objects.create_user('func', 'func@test.com', 'pass123')

        self.pessoa_gestor = Pessoa.objects.create(user=self.user_gestor, nome='Gestor', is_gestor=True)
        self.pessoa_gestor.empresas.add(self.neuraxo, self.rw6)
        PapelEmpresa.objects.create(pessoa=self.pessoa_gestor, empresa=self.neuraxo, papel='gestor')
        PapelEmpresa.objects.create(pessoa=self.pessoa_gestor, empresa=self.rw6, papel='gestor')

        self.pessoa_func = Pessoa.objects.create(user=self.user_func, nome='Funcionario')
        self.pessoa_func.empresas.add(self.neuraxo)
        PapelEmpresa.objects.create(pessoa=self.pessoa_func, empresa=self.neuraxo, papel='executante')

        self.c = TestClient(SERVER_NAME='core.neuraxo.com.br')
        self.H = 'core.neuraxo.com.br'


class RotinaTemplateTests(BaseTestCase):
    """Testes de criação e geração de rotinas"""

    def test_criar_template(self):
        t = ChecklistTemplate.objects.create(
            empresa=self.neuraxo, titulo='Verificar emails',
            recorrencia='diaria', responsavel=self.pessoa_func,
        )
        self.assertEqual(t.titulo, 'Verificar emails')

    def test_template_com_horario(self):
        t = ChecklistTemplate.objects.create(
            empresa=self.neuraxo, titulo='Reuniao',
            recorrencia='diaria', responsavel=self.pessoa_gestor,
            horario_sugerido='09:00',
        )
        self.assertIsNotNone(t.horario_sugerido)

    def test_template_com_subtarefas(self):
        t = ChecklistTemplate.objects.create(
            empresa=self.neuraxo, titulo='Rotina manha',
            recorrencia='diaria', responsavel=self.pessoa_func,
        )
        SubTarefaTemplate.objects.create(template=t, titulo='Abrir sistema', ordem=0)
        SubTarefaTemplate.objects.create(template=t, titulo='Conferir pedidos', ordem=1)
        SubTarefaTemplate.objects.create(template=t, titulo='Responder emails', ordem=2)
        self.assertEqual(t.subtarefas_template.count(), 3)

    def test_gerar_tarefa_dia(self):
        t = ChecklistTemplate.objects.create(
            empresa=self.neuraxo, titulo='Tarefa teste',
            recorrencia='diaria', responsavel=self.pessoa_func,
        )
        hoje = timezone.localdate()
        item = ChecklistItem.objects.create(
            template=t, responsavel=self.pessoa_func,
            data_referencia=hoje,
            data_limite=timezone.now() + timedelta(hours=8),
        )
        self.assertEqual(item.responsavel, self.pessoa_func)
        self.assertEqual(item.data_referencia, hoje)

    def test_subtarefas_copiadas_para_item(self):
        t = ChecklistTemplate.objects.create(
            empresa=self.neuraxo, titulo='Rotina',
            recorrencia='diaria', responsavel=self.pessoa_func,
        )
        SubTarefaTemplate.objects.create(template=t, titulo='Etapa 1', ordem=0)
        SubTarefaTemplate.objects.create(template=t, titulo='Etapa 2', ordem=1)

        item = ChecklistItem.objects.create(
            template=t, responsavel=self.pessoa_func,
            data_referencia=timezone.localdate(),
            data_limite=timezone.now() + timedelta(hours=8),
        )
        for st in t.subtarefas_template.all():
            SubTarefa.objects.create(checklist_item=item, titulo=st.titulo, ordem=st.ordem)
        self.assertEqual(item.subtarefas.count(), 2)

    def test_ordenacao_por_horario(self):
        ChecklistTemplate.objects.create(
            empresa=self.neuraxo, titulo='Tarde', recorrencia='diaria',
            responsavel=self.pessoa_func, horario_sugerido='14:00',
        )
        ChecklistTemplate.objects.create(
            empresa=self.neuraxo, titulo='Manha', recorrencia='diaria',
            responsavel=self.pessoa_func, horario_sugerido='08:00',
        )
        templates = list(ChecklistTemplate.objects.filter(empresa=self.neuraxo))
        self.assertEqual(templates[0].titulo, 'Manha')
        self.assertEqual(templates[1].titulo, 'Tarde')


class RotinaViewTests(BaseTestCase):
    """Testes das views de rotina"""

    def test_rotina_diaria(self):
        self.c.login(username='gestor', password='pass123')
        r = self.c.get('/rotina/', SERVER_NAME=self.H)
        self.assertEqual(r.status_code, 200)

    def test_lista_rotinas_func_acessa(self):
        """Funcionário pode acessar rotinas (vê só as dele)"""
        self.c.login(username='func', password='pass123')
        r = self.c.get('/rotinas/', SERVER_NAME=self.H)
        self.assertIn(r.status_code, [200, 302])

    def test_criar_rotina_post(self):
        self.c.login(username='gestor', password='pass123')
        r = self.c.post('/rotinas/nova/', {
            'empresa': self.neuraxo.id,
            'titulo': 'Nova rotina teste',
            'recorrencia': 'diaria',
            'responsavel': self.pessoa_func.id,
            'ordem_execucao': 1,
            'tempo_estimado': 30,
            'prioridade': 2,
            'subtarefas_json': '["Passo 1","Passo 2"]',
        }, SERVER_NAME=self.H)
        self.assertEqual(r.status_code, 302)
        t = ChecklistTemplate.objects.get(titulo='Nova rotina teste')
        self.assertEqual(t.subtarefas_template.count(), 2)

    def test_reordenar_rotinas(self):
        import json
        t1 = ChecklistTemplate.objects.create(
            empresa=self.neuraxo, titulo='A', recorrencia='diaria',
            responsavel=self.pessoa_func, ordem_execucao=0,
        )
        t2 = ChecklistTemplate.objects.create(
            empresa=self.neuraxo, titulo='B', recorrencia='diaria',
            responsavel=self.pessoa_func, ordem_execucao=1,
        )
        self.c.login(username='gestor', password='pass123')
        r = self.c.post('/api/rotinas/reordenar/', json.dumps({
            'items': [{'id': t2.id, 'ordem': 0}, {'id': t1.id, 'ordem': 1}]
        }), content_type='application/json', SERVER_NAME=self.H)
        self.assertEqual(r.status_code, 200)
        t1.refresh_from_db()
        t2.refresh_from_db()
        self.assertEqual(t1.ordem_execucao, 1)
        self.assertEqual(t2.ordem_execucao, 0)


class DemandaTests(BaseTestCase):
    """Testes de demandas"""

    def test_criar_demanda(self):
        d = Demanda.objects.create(
            empresa=self.neuraxo, titulo='Feature X',
            responsavel=self.pessoa_func, solicitante=self.pessoa_gestor,
            prazo=timezone.now() + timedelta(days=7),
        )
        self.assertEqual(d.status, 'pendente')

    def test_demanda_atrasada(self):
        d = Demanda.objects.create(
            empresa=self.neuraxo, titulo='Atrasada',
            responsavel=self.pessoa_func, solicitante=self.pessoa_gestor,
            prazo=timezone.now() - timedelta(days=1),
        )
        self.assertTrue(d.esta_atrasada())

    def test_demanda_no_prazo(self):
        d = Demanda.objects.create(
            empresa=self.neuraxo, titulo='No prazo',
            responsavel=self.pessoa_func, solicitante=self.pessoa_gestor,
            prazo=timezone.now() + timedelta(days=7),
        )
        self.assertFalse(d.esta_atrasada())

    def test_notificacao_ao_criar_demanda(self):
        Demanda.objects.create(
            empresa=self.neuraxo, titulo='Notifica',
            responsavel=self.pessoa_func, solicitante=self.pessoa_gestor,
            prazo=timezone.now() + timedelta(days=3),
        )
        notifs = NotificacaoInApp.objects.filter(destinatario=self.pessoa_func, tipo='demanda')
        self.assertTrue(notifs.exists())

    def test_sem_notificacao_se_criador_e_responsavel(self):
        Demanda.objects.create(
            empresa=self.neuraxo, titulo='Auto',
            responsavel=self.pessoa_gestor, solicitante=self.pessoa_gestor,
            prazo=timezone.now() + timedelta(days=3),
        )
        notifs = NotificacaoInApp.objects.filter(destinatario=self.pessoa_gestor, tipo='demanda')
        self.assertFalse(notifs.exists())

    def test_lista_demandas(self):
        self.c.login(username='gestor', password='pass123')
        r = self.c.get('/demandas/', SERVER_NAME=self.H)
        self.assertEqual(r.status_code, 200)

    def test_filtro_empresa_demandas(self):
        Demanda.objects.create(
            empresa=self.neuraxo, titulo='Neuraxo D',
            responsavel=self.pessoa_gestor, solicitante=self.pessoa_gestor,
            prazo=timezone.now() + timedelta(days=3),
        )
        Demanda.objects.create(
            empresa=self.rw6, titulo='RW6 D',
            responsavel=self.pessoa_gestor, solicitante=self.pessoa_gestor,
            prazo=timezone.now() + timedelta(days=3),
        )
        self.c.login(username='gestor', password='pass123')
        self.c.get(f'/empresa/{self.neuraxo.id}/ativar/', SERVER_NAME=self.H)
        r = self.c.get('/demandas/', SERVER_NAME=self.H)
        self.assertEqual(r.status_code, 200)


class ProjetoTests(BaseTestCase):
    """Testes de projetos"""

    def test_criar_projeto(self):
        p = Projeto.objects.create(
            empresa=self.neuraxo, titulo='Projeto X', responsavel=self.pessoa_gestor,
        )
        self.assertEqual(p.status, 'planejamento')

    def test_lista_projetos(self):
        self.c.login(username='gestor', password='pass123')
        r = self.c.get('/projetos/', SERVER_NAME=self.H)
        self.assertEqual(r.status_code, 200)


class IDORTests(BaseTestCase):
    """Isolamento multi-tenant: gestor de uma empresa NÃO acessa dados de outra.

    Prova as correções de IDOR (escopo por Empresa). 'Outra' é uma empresa em
    que pessoa_gestor (Neuraxo/RW6) NÃO participa. Toda ação cross-empresa deve
    dar 404 — e o dado-alvo NÃO pode mudar.
    """

    def setUp(self):
        super().setUp()
        import json as _json
        from datetime import date
        from checklists.models import (
            ChecklistTemplate, ChecklistItem, StatusItem, MapaMentalNo,
        )
        self._json = _json
        self._date = date
        self._StatusItem = StatusItem
        self._MapaMentalNo = MapaMentalNo

        # Empresa "Outra" + gestor próprio (estranho ao pessoa_gestor)
        self.outra = Empresa.objects.create(nome='Outra')
        self.user_outro = User.objects.create_user('outro', 'outro@test.com', 'pass123')
        self.pessoa_outro = Pessoa.objects.create(
            user=self.user_outro, nome='Gestor Outra', is_gestor=True,
        )
        self.pessoa_outro.empresas.add(self.outra)
        PapelEmpresa.objects.create(
            pessoa=self.pessoa_outro, empresa=self.outra, papel='gestor',
        )

        # Demanda da empresa Outra
        self.demanda_outra = Demanda.objects.create(
            empresa=self.outra, titulo='Demanda Outra',
            responsavel=self.pessoa_outro, solicitante=self.pessoa_outro,
            prazo=timezone.now() + timedelta(days=3),
        )

        # Projeto da empresa Outra (+ nó de mapa)
        self.projeto_outra = Projeto.objects.create(
            empresa=self.outra, titulo='Projeto Outra', responsavel=self.pessoa_outro,
        )
        self.no_outra = MapaMentalNo.objects.create(
            projeto=self.projeto_outra, titulo='No Outra',
        )

        # ChecklistItem da empresa Outra com cancelamento solicitado
        self.template_outra = ChecklistTemplate.objects.create(
            empresa=self.outra, titulo='Template Outra',
        )
        self.item_outra = ChecklistItem.objects.create(
            template=self.template_outra, responsavel=self.pessoa_outro,
            data_referencia=date.today(),
            data_limite=timezone.now() + timedelta(days=1),
            cancelamento_solicitado=True,
        )

        self.c.login(username='gestor', password='pass123')

    def _post_json(self, url, payload=None):
        return self.c.post(
            url, data=self._json.dumps(payload or {}),
            content_type='application/json', SERVER_NAME=self.H,
        )

    # ── Demanda ──────────────────────────────────────────────
    def test_comentario_demanda_outra_empresa_404(self):
        url = f'/demanda/{self.demanda_outra.id}/comentario/'
        r = self._post_json(url, {'texto': 'invasao'})
        self.assertEqual(r.status_code, 404)
        from checklists.models import ComentarioDemanda
        self.assertFalse(
            ComentarioDemanda.objects.filter(demanda=self.demanda_outra).exists()
        )

    # ── ChecklistItem (aprovar/recusar cancelamento) ─────────
    def test_aprovar_cancelamento_outra_empresa_404(self):
        url = f'/cancelar/{self.item_outra.id}/aprovar/'
        r = self._post_json(url)
        self.assertEqual(r.status_code, 404)
        self.item_outra.refresh_from_db()
        # status NÃO virou cancelado
        self.assertNotEqual(self.item_outra.status, self._StatusItem.CANCELADO)

    def test_recusar_cancelamento_outra_empresa_404(self):
        url = f'/cancelar/{self.item_outra.id}/recusar/'
        r = self._post_json(url)
        self.assertEqual(r.status_code, 404)
        self.item_outra.refresh_from_db()
        # solicitação de cancelamento NÃO foi mexida
        self.assertTrue(self.item_outra.cancelamento_solicitado)

    # ── Projeto ──────────────────────────────────────────────
    def test_mudar_status_projeto_outra_empresa_404(self):
        url = f'/projeto/{self.projeto_outra.id}/status/'
        r = self._post_json(url, {'status': 'concluido'})
        self.assertEqual(r.status_code, 404)
        self.projeto_outra.refresh_from_db()
        self.assertEqual(self.projeto_outra.status, 'planejamento')

    # ── MapaMentalNo ─────────────────────────────────────────
    def test_excluir_no_mapa_outra_empresa_404(self):
        url = f'/projeto/mapa/no/{self.no_outra.id}/excluir/'
        r = self._post_json(url)
        self.assertEqual(r.status_code, 404)
        self.assertTrue(self._MapaMentalNo.objects.filter(id=self.no_outra.id).exists())

    def test_editar_no_mapa_outra_empresa_404(self):
        url = f'/projeto/mapa/no/{self.no_outra.id}/editar/'
        r = self._post_json(url, {'titulo': 'hackeado'})
        self.assertEqual(r.status_code, 404)
        self.no_outra.refresh_from_db()
        self.assertEqual(self.no_outra.titulo, 'No Outra')

    # ── Caso de controle: ação na PRÓPRIA empresa funciona ───
    def test_mudar_status_projeto_propria_empresa_ok(self):
        proj = Projeto.objects.create(
            empresa=self.neuraxo, titulo='Projeto Meu', responsavel=self.pessoa_gestor,
        )
        url = f'/projeto/{proj.id}/status/'
        r = self._post_json(url, {'status': 'concluido'})
        self.assertEqual(r.status_code, 200)
        proj.refresh_from_db()
        self.assertEqual(proj.status, 'concluido')
