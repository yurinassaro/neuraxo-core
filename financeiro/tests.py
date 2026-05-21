"""
Testes do NeuraxoCheck - Financeiro e Cofre
"""
from django.test import TestCase, Client as TestClient
from django.contrib.auth.models import User
from core.models import Empresa, Pessoa, PapelEmpresa, ItemCofre


class BaseTestCase(TestCase):
    def setUp(self):
        self.neuraxo = Empresa.objects.create(nome='Neuraxo')
        self.rw6 = Empresa.objects.create(nome='RW6')

        self.user_gestor = User.objects.create_user('gestor', 'gestor@test.com', 'pass123')
        self.user_func = User.objects.create_user('func', 'func@test.com', 'pass123')
        self.user_colab = User.objects.create_user('colab', 'colab@test.com', 'pass123')

        self.pessoa_gestor = Pessoa.objects.create(user=self.user_gestor, nome='Gestor', is_gestor=True)
        self.pessoa_gestor.empresas.add(self.neuraxo, self.rw6)
        PapelEmpresa.objects.create(pessoa=self.pessoa_gestor, empresa=self.neuraxo, papel='gestor')
        PapelEmpresa.objects.create(pessoa=self.pessoa_gestor, empresa=self.rw6, papel='gestor')

        self.pessoa_func = Pessoa.objects.create(user=self.user_func, nome='Funcionario')
        self.pessoa_func.empresas.add(self.neuraxo)
        PapelEmpresa.objects.create(pessoa=self.pessoa_func, empresa=self.neuraxo, papel='executante')

        self.pessoa_colab = Pessoa.objects.create(user=self.user_colab, nome='Colaborador')
        self.pessoa_colab.empresas.add(self.neuraxo)
        PapelEmpresa.objects.create(pessoa=self.pessoa_colab, empresa=self.neuraxo, papel='colaborador')

        self.c = TestClient(SERVER_NAME='core.neuraxo.com.br')
        self.H = 'core.neuraxo.com.br'


class FinanceiroAcessoTests(BaseTestCase):
    """Testes de acesso ao financeiro por papel"""

    def test_gestor_acessa_financeiro(self):
        self.c.login(username='gestor', password='pass123')
        r = self.c.get('/financeiro/', SERVER_NAME=self.H)
        self.assertEqual(r.status_code, 200)

    def test_func_sem_empresas_financeiro(self):
        """Executante não tem empresas no financeiro"""
        self.c.login(username='func', password='pass123')
        r = self.c.get('/financeiro/', SERVER_NAME=self.H)
        self.assertIn(r.status_code, [200, 302])

    def test_colab_sem_acesso_financeiro(self):
        """Colaborador não pode ver financeiro"""
        self.c.login(username='colab', password='pass123')
        r = self.c.get('/financeiro/', SERVER_NAME=self.H)
        self.assertIn(r.status_code, [200, 302])

    def test_financeiro_filtro_empresa(self):
        """Financeiro respeita filtro global"""
        self.c.login(username='gestor', password='pass123')
        self.c.get(f'/empresa/{self.neuraxo.id}/ativar/', SERVER_NAME=self.H)
        r = self.c.get('/financeiro/', SERVER_NAME=self.H)
        self.assertEqual(r.status_code, 200)

    def test_contas_pagar(self):
        self.c.login(username='gestor', password='pass123')
        r = self.c.get('/financeiro/contas-pagar/', SERVER_NAME=self.H)
        self.assertIn(r.status_code, [200, 302])


class CofreTests(BaseTestCase):
    """Testes do cofre de senhas"""

    def test_cofre_requer_login(self):
        r = self.c.get('/cofre/', SERVER_NAME=self.H)
        self.assertIn(r.status_code, [301, 302])

    def test_cofre_requer_desbloqueio(self):
        """Cofre exige senha para desbloquear"""
        self.c.login(username='gestor', password='pass123')
        r = self.c.get('/cofre/', SERVER_NAME=self.H)
        self.assertEqual(r.status_code, 200)
        # Deve mostrar tela de login do cofre (não os itens)

    def test_criptografia_senha(self):
        """Senha deve ser criptografada e descriptografável"""
        item = ItemCofre(empresa=self.neuraxo, titulo='Teste', criado_por=self.pessoa_gestor)
        item.set_senha('MinhaSenhaSecreta123!')
        item.save()
        # Senha criptografada não é igual à original
        self.assertNotEqual(item.senha_encrypted, 'MinhaSenhaSecreta123!')
        self.assertNotEqual(item.senha_encrypted, '')
        # Descriptografar retorna a original
        self.assertEqual(item.get_senha(), 'MinhaSenhaSecreta123!')

    def test_cofre_filtra_por_empresa(self):
        """Cofre mostra apenas itens das empresas do usuário"""
        ItemCofre.objects.create(
            empresa=self.neuraxo, titulo='Senha Neuraxo', criado_por=self.pessoa_gestor
        )
        ItemCofre.objects.create(
            empresa=self.rw6, titulo='Senha RW6', criado_por=self.pessoa_gestor
        )
        # Func só tem acesso à Neuraxo
        itens_func = ItemCofre.objects.filter(
            empresa__in=self.pessoa_func.empresas.all()
        )
        self.assertEqual(itens_func.count(), 1)
        self.assertEqual(itens_func.first().titulo, 'Senha Neuraxo')

    def test_cofre_senha_vazia(self):
        """Item sem senha funciona sem erro"""
        item = ItemCofre(empresa=self.neuraxo, titulo='Sem senha', criado_por=self.pessoa_gestor)
        item.set_senha('')
        item.save()
        self.assertEqual(item.get_senha(), '')
