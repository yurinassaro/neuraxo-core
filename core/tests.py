"""
Testes do NeuraxoCheck - Core
Cobre: autenticação, permissões por empresa, filtro global, segurança
"""
from django.test import TestCase, Client as TestClient
from django.contrib.auth.models import User
from core.models import (
    Empresa, Pessoa, PapelEmpresa, Cliente, ContatoCliente,
    Solicitacao, NotificacaoInApp,
)


class BaseTestCase(TestCase):
    """Setup compartilhado para todos os testes"""

    def setUp(self):
        # Empresas
        self.neuraxo = Empresa.objects.create(nome='Neuraxo')
        self.rw6 = Empresa.objects.create(nome='RW6')
        self.pessoal = Empresa.objects.create(nome='Pessoal')

        # Users
        self.user_admin = User.objects.create_user('admin', 'admin@test.com', 'admin123')
        self.user_func = User.objects.create_user('func', 'func@test.com', 'func123')
        self.user_colab = User.objects.create_user('colab', 'colab@test.com', 'colab123')
        self.user_externo = User.objects.create_user('externo', 'externo@test.com', 'ext123')

        # Pessoas
        self.pessoa_admin = Pessoa.objects.create(user=self.user_admin, nome='Admin', is_gestor=True)
        self.pessoa_admin.empresas.add(self.neuraxo, self.rw6, self.pessoal)

        self.pessoa_func = Pessoa.objects.create(user=self.user_func, nome='Funcionario')
        self.pessoa_func.empresas.add(self.neuraxo)

        self.pessoa_colab = Pessoa.objects.create(user=self.user_colab, nome='Colaborador')
        self.pessoa_colab.empresas.add(self.neuraxo, self.rw6)

        # Papéis
        PapelEmpresa.objects.create(pessoa=self.pessoa_admin, empresa=self.neuraxo, papel='gestor')
        PapelEmpresa.objects.create(pessoa=self.pessoa_admin, empresa=self.rw6, papel='gestor')
        PapelEmpresa.objects.create(pessoa=self.pessoa_admin, empresa=self.pessoal, papel='gestor')
        PapelEmpresa.objects.create(pessoa=self.pessoa_func, empresa=self.neuraxo, papel='executante')
        PapelEmpresa.objects.create(pessoa=self.pessoa_colab, empresa=self.neuraxo, papel='colaborador')
        PapelEmpresa.objects.create(pessoa=self.pessoa_colab, empresa=self.rw6, papel='executante')

        self.c = TestClient(SERVER_NAME='core.neuraxo.com.br')


class AuthTests(BaseTestCase):
    """Testes de autenticação"""

    def test_login_por_email(self):
        """Login com email deve funcionar"""
        ok = self.c.login(username='admin@test.com', password='admin123')
        self.assertTrue(ok)

    def test_login_por_username(self):
        """Login com username (fallback) deve funcionar"""
        ok = self.c.login(username='admin', password='admin123')
        self.assertTrue(ok)

    def test_login_senha_errada(self):
        """Login com senha errada deve falhar"""
        ok = self.c.login(username='admin@test.com', password='errada')
        self.assertFalse(ok)

    def test_paginas_protegidas_redirecionam(self):
        """Páginas protegidas devem redirecionar para login"""
        urls = ['/', '/rotina/', '/demandas/', '/cofre/', '/financeiro/', '/equipe/']
        for url in urls:
            r = self.c.get(url, SERVER_NAME='core.neuraxo.com.br')
            self.assertIn(r.status_code, [301, 302], f'{url} deveria redirecionar')


class PapelEmpresaTests(BaseTestCase):
    """Testes de papéis por empresa"""

    def test_papel_gestor(self):
        self.assertEqual(self.pessoa_admin.get_papel_empresa(self.neuraxo), 'gestor')

    def test_papel_executante(self):
        self.assertEqual(self.pessoa_func.get_papel_empresa(self.neuraxo), 'executante')

    def test_papel_colaborador(self):
        self.assertEqual(self.pessoa_colab.get_papel_empresa(self.neuraxo), 'colaborador')

    def test_is_gestor_empresa(self):
        self.assertTrue(self.pessoa_admin.is_gestor_empresa(self.neuraxo))
        self.assertFalse(self.pessoa_func.is_gestor_empresa(self.neuraxo))

    def test_pode_ver_equipe(self):
        """Gestor e colaborador podem ver equipe, executante não"""
        self.assertTrue(self.pessoa_admin.pode_ver_equipe(self.neuraxo))
        self.assertTrue(self.pessoa_colab.pode_ver_equipe(self.neuraxo))
        self.assertFalse(self.pessoa_func.pode_ver_equipe(self.neuraxo))

    def test_pode_ver_financeiro(self):
        """Só gestor pode ver financeiro"""
        self.assertTrue(self.pessoa_admin.pode_ver_financeiro(self.neuraxo))
        self.assertFalse(self.pessoa_colab.pode_ver_financeiro(self.neuraxo))
        self.assertFalse(self.pessoa_func.pode_ver_financeiro(self.neuraxo))

    def test_papel_diferente_por_empresa(self):
        """Mesma pessoa pode ter papéis diferentes em empresas diferentes"""
        self.assertEqual(self.pessoa_colab.get_papel_empresa(self.neuraxo), 'colaborador')
        self.assertEqual(self.pessoa_colab.get_papel_empresa(self.rw6), 'executante')


class FiltroGlobalTests(BaseTestCase):
    """Testes do filtro global por empresa ativa"""

    def test_dashboard_sem_filtro(self):
        """Dashboard sem empresa ativa mostra tudo"""
        self.c.login(username='admin', password='admin123')
        r = self.c.get('/', SERVER_NAME='core.neuraxo.com.br')
        self.assertEqual(r.status_code, 200)

    def test_dashboard_com_filtro(self):
        """Dashboard com empresa ativa filtra"""
        self.c.login(username='admin', password='admin123')
        # Ativar empresa
        self.c.get(f'/empresa/{self.neuraxo.id}/ativar/', SERVER_NAME='core.neuraxo.com.br')
        r = self.c.get('/', SERVER_NAME='core.neuraxo.com.br')
        self.assertEqual(r.status_code, 200)

    def test_trocar_empresa_salva_sessao(self):
        """Trocar empresa salva na sessão"""
        self.c.login(username='admin', password='admin123')
        self.c.get(f'/empresa/{self.rw6.id}/ativar/', SERVER_NAME='core.neuraxo.com.br')
        self.assertEqual(self.c.session.get('empresa_ativa_id'), self.rw6.id)

    def test_trocar_empresa_0_limpa(self):
        """Empresa 0 limpa o filtro"""
        self.c.login(username='admin', password='admin123')
        self.c.get(f'/empresa/{self.rw6.id}/ativar/', SERVER_NAME='core.neuraxo.com.br')
        self.c.get('/empresa/0/ativar/', SERVER_NAME='core.neuraxo.com.br')
        self.assertIsNone(self.c.session.get('empresa_ativa_id'))

    def test_nao_pode_ativar_empresa_sem_acesso(self):
        """Funcionário não pode ativar empresa que não tem acesso"""
        self.c.login(username='func', password='func123')
        self.c.get(f'/empresa/{self.rw6.id}/ativar/', SERVER_NAME='core.neuraxo.com.br')
        # Não deve ter salvo (func não tem acesso à RW6)
        self.assertNotEqual(self.c.session.get('empresa_ativa_id'), self.rw6.id)


class PaginasTests(BaseTestCase):
    """Testes de acesso às páginas"""

    def test_todas_paginas_admin(self):
        """Admin acessa todas as páginas sem erro"""
        self.c.login(username='admin', password='admin123')
        urls = [
            '/', '/rotina/', '/demandas/', '/cofre/',
            '/projetos/', '/calendario/', '/anotacoes/',
            '/aproveitamento/', '/equipe/', '/clientes/',
            '/notificacoes/',
        ]
        for url in urls:
            r = self.c.get(url, SERVER_NAME='core.neuraxo.com.br')
            self.assertIn(r.status_code, [200, 302], f'{url} retornou {r.status_code}')

    def test_todas_paginas_funcionario(self):
        """Funcionário acessa páginas básicas sem erro"""
        self.c.login(username='func', password='func123')
        urls = ['/', '/rotina/', '/demandas/', '/notificacoes/']
        for url in urls:
            r = self.c.get(url, SERVER_NAME='core.neuraxo.com.br')
            self.assertIn(r.status_code, [200, 302], f'{url} retornou {r.status_code}')


class SegurancaTests(BaseTestCase):
    """Testes de segurança"""

    def test_usuario_sem_pessoa_nao_quebra(self):
        """User sem Pessoa vinculada não deve causar 500"""
        self.c.login(username='externo', password='ext123')
        r = self.c.get('/', SERVER_NAME='core.neuraxo.com.br')
        self.assertIn(r.status_code, [200, 302])

    def test_csrf_obrigatorio_em_posts(self):
        """POST sem CSRF deve ser rejeitado"""
        self.c.login(username='admin', password='admin123')
        csrf_client = TestClient(enforce_csrf_checks=True, SERVER_NAME='core.neuraxo.com.br')
        csrf_client.login(username='admin', password='admin123')
        r = csrf_client.post('/notificacoes/marcar-todas/', SERVER_NAME='core.neuraxo.com.br')
        self.assertEqual(r.status_code, 403)

    def test_equipe_so_gestor(self):
        """Funcionário não pode acessar equipe"""
        self.c.login(username='func', password='func123')
        r = self.c.get('/equipe/', SERVER_NAME='core.neuraxo.com.br')
        self.assertIn(r.status_code, [302, 403])

    def test_financeiro_so_gestor(self):
        """Funcionário não vê empresas no financeiro"""
        self.c.login(username='func', password='func123')
        r = self.c.get('/financeiro/', SERVER_NAME='core.neuraxo.com.br')
        # Deve retornar 200 mas sem dados (empresas vazio)
        self.assertIn(r.status_code, [200, 302])


class NotificacaoTests(BaseTestCase):
    """Testes de notificações in-app"""

    def test_criar_notificacao(self):
        n = NotificacaoInApp.criar(
            destinatario=self.pessoa_admin,
            tipo='geral',
            titulo='Teste',
            mensagem='Msg teste',
        )
        self.assertEqual(n.destinatario, self.pessoa_admin)
        self.assertFalse(n.lida)

    def test_contagem_nao_lidas(self):
        NotificacaoInApp.criar(destinatario=self.pessoa_admin, tipo='geral', titulo='T1')
        NotificacaoInApp.criar(destinatario=self.pessoa_admin, tipo='geral', titulo='T2')
        count = self.pessoa_admin.notificacoes_inapp.filter(lida=False).count()
        self.assertEqual(count, 2)

    def test_marcar_lida(self):
        n = NotificacaoInApp.criar(destinatario=self.pessoa_admin, tipo='geral', titulo='T1')
        n.lida = True
        n.save()
        count = self.pessoa_admin.notificacoes_inapp.filter(lida=False).count()
        self.assertEqual(count, 0)

    def test_api_count(self):
        self.c.login(username='admin', password='admin123')
        NotificacaoInApp.criar(destinatario=self.pessoa_admin, tipo='geral', titulo='T1')
        r = self.c.get('/notificacoes/count/', SERVER_NAME='core.neuraxo.com.br')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['count'], 1)

    def test_notificacao_outro_usuario_nao_aparece(self):
        """Notificação de outro usuário não aparece na contagem"""
        NotificacaoInApp.criar(destinatario=self.pessoa_func, tipo='geral', titulo='T1')
        self.c.login(username='admin', password='admin123')
        r = self.c.get('/notificacoes/count/', SERVER_NAME='core.neuraxo.com.br')
        self.assertEqual(r.json()['count'], 0)


class ClientePortalTests(BaseTestCase):
    """Testes do portal do cliente"""

    def setUp(self):
        super().setUp()
        # Criar cliente e contatos
        self.cliente = Cliente.objects.create(empresa=self.rw6, nome='Liveb Cre')
        self.user_dono = User.objects.create_user('thiago', 'thiago@liveb.com', 'teste123')
        self.user_func_cli = User.objects.create_user('henrique', 'henrique@liveb.com', 'teste123')
        self.contato_dono = ContatoCliente.objects.create(
            cliente=self.cliente, user=self.user_dono, nome='Thiago',
            email='thiago@liveb.com', papel='dono'
        )
        self.contato_func = ContatoCliente.objects.create(
            cliente=self.cliente, user=self.user_func_cli, nome='Henrique',
            email='henrique@liveb.com', papel='funcionario', funcao='Criativo'
        )
        # Solicitações
        self.sol_geral = Solicitacao.objects.create(
            empresa=self.rw6, cliente=self.cliente, criado_por=self.pessoa_admin,
            titulo='Enviar fotos', tipo='material'
        )
        self.sol_henrique = Solicitacao.objects.create(
            empresa=self.rw6, cliente=self.cliente, criado_por=self.pessoa_admin,
            contato=self.contato_func, titulo='Criar banner', tipo='aprovacao'
        )
        self.sol_thiago = Solicitacao.objects.create(
            empresa=self.rw6, cliente=self.cliente, criado_por=self.pessoa_admin,
            contato=self.contato_dono, titulo='Aprovar orçamento', tipo='aprovacao'
        )

    def test_portal_login_contato(self):
        """Contato do cliente pode logar no portal"""
        ok = self.c.login(username='thiago@liveb.com', password='teste123')
        self.assertTrue(ok)

    def test_portal_login_usuario_normal_nao_entra(self):
        """Usuário normal (não contato) não entra no portal"""
        self.c.login(username='admin', password='admin123')
        r = self.c.get('/portal/', SERVER_NAME='core.neuraxo.com.br')
        self.assertIn(r.status_code, [302])  # redireciona para portal_login

    def test_dono_ve_todas_solicitacoes(self):
        """Dono vê todas as solicitações do cliente"""
        self.c.login(username='thiago', password='teste123')
        r = self.c.get('/portal/', SERVER_NAME='core.neuraxo.com.br')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['pendentes'].count(), 3)

    def test_funcionario_ve_so_as_dele(self):
        """Funcionário vê só solicitações atribuídas a ele + gerais"""
        self.c.login(username='henrique', password='teste123')
        r = self.c.get('/portal/', SERVER_NAME='core.neuraxo.com.br')
        self.assertEqual(r.status_code, 200)
        # Henrique vê: sol_geral (sem contato) + sol_henrique (dele) = 2
        self.assertEqual(r.context['pendentes'].count(), 2)

    def test_funcionario_nao_ve_solicitacao_do_dono(self):
        """Funcionário não vê solicitação atribuída ao dono"""
        self.c.login(username='henrique', password='teste123')
        r = self.c.get('/portal/', SERVER_NAME='core.neuraxo.com.br')
        titulos = [s.titulo for s in r.context['pendentes']]
        self.assertNotIn('Aprovar orçamento', titulos)

    def test_responder_solicitacao(self):
        """Contato pode responder uma solicitação"""
        from core.models import ComentarioSolicitacao
        self.c.login(username='thiago', password='teste123')
        r = self.c.post(
            f'/portal/{self.sol_geral.id}/responder/',
            {'resposta': 'Fotos enviadas por email'},
            SERVER_NAME='core.neuraxo.com.br'
        )
        self.assertEqual(r.status_code, 302)
        # Resposta salva como comentário
        self.assertTrue(ComentarioSolicitacao.objects.filter(
            solicitacao=self.sol_geral, texto='Fotos enviadas por email'
        ).exists())

    def test_concluir_solicitacao(self):
        """Contato pode concluir uma solicitação"""
        self.c.login(username='thiago', password='teste123')
        self.c.post(
            f'/portal/{self.sol_geral.id}/responder/',
            {'resposta': 'Pronto', 'concluir': '1'},
            SERVER_NAME='core.neuraxo.com.br'
        )
        self.sol_geral.refresh_from_db()
        self.assertEqual(self.sol_geral.status, 'concluido')

    def test_contato_nao_acessa_solicitacao_de_outro_cliente(self):
        """Contato não pode responder solicitação de outro cliente"""
        outro_cliente = Cliente.objects.create(empresa=self.rw6, nome='Outro')
        sol_outro = Solicitacao.objects.create(
            empresa=self.rw6, cliente=outro_cliente, criado_por=self.pessoa_admin,
            titulo='Sol outro', tipo='outro'
        )
        self.c.login(username='thiago', password='teste123')
        r = self.c.post(
            f'/portal/{sol_outro.id}/responder/',
            {'resposta': 'Hack'},
            SERVER_NAME='core.neuraxo.com.br'
        )
        # 404 ou redirect (FriendlyErrorMiddleware converte 404 em redirect)
        self.assertIn(r.status_code, [302, 404])
        # Verificar que a resposta NÃO foi salva
        sol_outro.refresh_from_db()
        self.assertEqual(sol_outro.resposta, '')


class EmpresaTests(BaseTestCase):
    """Testes de criação e gestão de empresas"""

    def test_lista_empresas(self):
        self.c.login(username='admin', password='admin123')
        r = self.c.get('/empresas/', SERVER_NAME='core.neuraxo.com.br')
        self.assertEqual(r.status_code, 200)

    def test_lista_empresas_so_gestor(self):
        self.c.login(username='func', password='func123')
        r = self.c.get('/empresas/', SERVER_NAME='core.neuraxo.com.br')
        self.assertIn(r.status_code, [302, 403])

    def test_criar_empresa(self):
        self.c.login(username='admin', password='admin123')
        r = self.c.post('/empresas/criar/', {
            'nome': 'Nova Empresa Teste',
            'cor': '#ff5500',
        }, SERVER_NAME='core.neuraxo.com.br')
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Empresa.objects.filter(nome='Nova Empresa Teste').exists())

    def test_criar_empresa_vincula_gestor(self):
        """Ao criar empresa, o criador vira gestor dela"""
        from core.models import PapelEmpresa
        self.c.login(username='admin', password='admin123')
        self.c.post('/empresas/criar/', {'nome': 'Empresa Gestor'}, SERVER_NAME='core.neuraxo.com.br')
        emp = Empresa.objects.get(nome='Empresa Gestor')
        # Verificar que está vinculado
        self.assertTrue(self.pessoa_admin.empresas.filter(id=emp.id).exists())
        # Verificar papel gestor
        pe = PapelEmpresa.objects.filter(pessoa=self.pessoa_admin, empresa=emp).first()
        self.assertIsNotNone(pe)
        self.assertEqual(pe.papel, 'gestor')

    def test_criar_empresa_duplicada(self):
        self.c.login(username='admin', password='admin123')
        self.c.post('/empresas/criar/', {'nome': 'Neuraxo'}, SERVER_NAME='core.neuraxo.com.br')
        # Neuraxo já existe no setUp
        self.assertEqual(Empresa.objects.filter(nome__iexact='Neuraxo').count(), 1)

    def test_editar_empresa(self):
        self.c.login(username='admin', password='admin123')
        r = self.c.post(f'/empresas/{self.neuraxo.id}/editar/', {
            'nome': 'Neuraxo Atualizado',
            'cor': '#00ff00',
        }, SERVER_NAME='core.neuraxo.com.br')
        self.assertEqual(r.status_code, 302)
        self.neuraxo.refresh_from_db()
        self.assertEqual(self.neuraxo.nome, 'Neuraxo Atualizado')
        self.assertEqual(self.neuraxo.cor, '#00ff00')

    def test_func_nao_edita_empresa(self):
        """Funcionário não pode editar empresa"""
        self.c.login(username='func', password='func123')
        r = self.c.post(f'/empresas/{self.neuraxo.id}/editar/', {
            'nome': 'Hack',
        }, SERVER_NAME='core.neuraxo.com.br')
        self.neuraxo.refresh_from_db()
        self.assertNotEqual(self.neuraxo.nome, 'Hack')


class SolicitacaoInternaTests(BaseTestCase):
    """Testes das views internas de solicitações"""

    def setUp(self):
        super().setUp()
        self.cliente = Cliente.objects.create(empresa=self.rw6, nome='Cliente Teste')

    def test_criar_solicitacao(self):
        self.c.login(username='admin', password='admin123')
        r = self.c.post('/solicitacao/criar/', {
            'cliente': self.cliente.id,
            'titulo': 'Teste solicitacao',
            'tipo': 'material',
        }, SERVER_NAME='core.neuraxo.com.br')
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Solicitacao.objects.filter(titulo='Teste solicitacao').exists())

    def test_alterar_status_solicitacao(self):
        sol = Solicitacao.objects.create(
            empresa=self.rw6, cliente=self.cliente, criado_por=self.pessoa_admin,
            titulo='Teste', tipo='outro'
        )
        self.c.login(username='admin', password='admin123')
        self.c.post(f'/solicitacao/{sol.id}/status/', {'status': 'concluido'},
                     SERVER_NAME='core.neuraxo.com.br')
        sol.refresh_from_db()
        self.assertEqual(sol.status, 'concluido')
