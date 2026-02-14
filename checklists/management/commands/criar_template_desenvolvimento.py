"""
Cria template completo de Desenvolvimento de Sistemas.
Uso: python manage.py criar_template_desenvolvimento
"""
from django.core.management.base import BaseCommand
from checklists.models import ProjetoTemplate, EtapaTemplate


class Command(BaseCommand):
    help = 'Cria template de Desenvolvimento de Sistemas completo'

    def handle(self, *args, **options):
        # Verificar se já existe
        if ProjetoTemplate.objects.filter(titulo__icontains='Desenvolvimento de Sistema').exists():
            self.stdout.write(self.style.WARNING('Template já existe. Pulando criação.'))
            return

        template = ProjetoTemplate.objects.create(
            titulo='Desenvolvimento de Sistema Completo',
            descricao='Template completo para projetos de desenvolvimento de software. '
                      'Inclui todas as fases: levantamento de requisitos, arquitetura, '
                      'desenvolvimento, testes, segurança, deploy e manutenção. '
                      'Cada etapa contém documentação detalhada de como executar.',
            cor='#059669',  # Verde esmeralda
            ativo=True,
        )

        etapas = [
            # =====================================
            # FASE 1: DESCOBERTA E PLANEJAMENTO
            # =====================================
            {
                'ordem': 1,
                'titulo': 'Kickoff e Alinhamento Inicial',
                'tempo_estimado': 120,
                'descricao': '''OBJETIVO: Alinhar expectativas e entender o contexto do projeto.

ATIVIDADES:
1. Reunião de kickoff com stakeholders
2. Apresentação da equipe e papéis
3. Definir canais de comunicação (Slack, email, reuniões)
4. Alinhar expectativas de prazo e escopo
5. Identificar riscos iniciais
6. Definir critérios de sucesso do projeto

ENTREGÁVEIS:
- Ata de reunião com decisões
- Lista de stakeholders e contatos
- Cronograma macro inicial
- Matriz de comunicação

DICAS:
- Grave a reunião (com permissão)
- Documente TUDO que for decidido
- Confirme entendimento por escrito'''
            },
            {
                'ordem': 2,
                'titulo': 'Levantamento de Requisitos Funcionais',
                'tempo_estimado': 480,
                'descricao': '''OBJETIVO: Documentar todas as funcionalidades que o sistema deve ter.

ATIVIDADES:
1. Entrevistas com usuários finais
2. Análise de processos atuais (AS-IS)
3. Workshops de requisitos
4. Documentar casos de uso principais
5. Criar user stories (formato: Como [usuário], quero [ação], para [benefício])
6. Priorizar requisitos (MoSCoW: Must, Should, Could, Won't)

ENTREGÁVEIS:
- Documento de Requisitos Funcionais (DRF)
- Lista de User Stories priorizadas
- Diagrama de casos de uso
- Glossário de termos do negócio

TEMPLATE USER STORY:
```
Título: [Nome da funcionalidade]
Como: [tipo de usuário]
Quero: [ação/funcionalidade]
Para: [benefício/valor]

Critérios de Aceite:
- [ ] Critério 1
- [ ] Critério 2

Regras de Negócio:
- RN01: [descrição]
```

PERGUNTAS CHAVE:
- Quem são os usuários do sistema?
- Quais problemas o sistema deve resolver?
- Quais são os fluxos críticos?
- Existem integrações necessárias?'''
            },
            {
                'ordem': 3,
                'titulo': 'Levantamento de Requisitos Não-Funcionais',
                'tempo_estimado': 240,
                'descricao': '''OBJETIVO: Definir requisitos de qualidade, performance e restrições técnicas.

CATEGORIAS A ANALISAR:

1. PERFORMANCE
   - Tempo de resposta esperado (ex: < 2s)
   - Throughput (requisições/segundo)
   - Usuários simultâneos esperados
   - Volume de dados (atual e projeção 5 anos)

2. DISPONIBILIDADE
   - SLA esperado (99.9%? 99.99%?)
   - Janela de manutenção permitida
   - RPO (Recovery Point Objective) - máximo de dados que pode perder
   - RTO (Recovery Time Objective) - tempo máximo offline

3. SEGURANÇA
   - Requisitos de autenticação (SSO, 2FA, etc)
   - Níveis de acesso/permissões
   - Dados sensíveis (LGPD, PCI-DSS)
   - Auditoria necessária

4. ESCALABILIDADE
   - Crescimento esperado
   - Picos de uso (sazonalidade)

5. COMPATIBILIDADE
   - Navegadores suportados
   - Dispositivos (desktop, mobile, tablet)
   - Sistemas operacionais
   - Integrações obrigatórias

6. MANUTENIBILIDADE
   - Documentação exigida
   - Padrões de código
   - Cobertura de testes mínima

ENTREGÁVEIS:
- Documento de Requisitos Não-Funcionais
- Matriz de rastreabilidade
- SLAs definidos'''
            },
            {
                'ordem': 4,
                'titulo': 'Análise de Viabilidade Técnica',
                'tempo_estimado': 180,
                'descricao': '''OBJETIVO: Validar se o projeto é tecnicamente viável e identificar desafios.

ATIVIDADES:

1. ANÁLISE DE COMPLEXIDADE
   - Mapear integrações necessárias
   - Identificar dependências externas
   - Avaliar APIs de terceiros
   - Verificar limitações técnicas

2. PROVA DE CONCEITO (se necessário)
   - Criar POC para funcionalidades críticas
   - Testar integrações complexas
   - Validar performance esperada

3. ANÁLISE DE RISCOS TÉCNICOS
   - Tecnologias novas/desconhecidas
   - Dependência de fornecedores
   - Limitações de infraestrutura
   - Gaps de conhecimento da equipe

4. ESTIMATIVA DE ESFORÇO
   - Quebrar em componentes
   - Estimar por funcionalidade
   - Adicionar buffer para riscos (20-30%)

ENTREGÁVEIS:
- Relatório de viabilidade técnica
- Resultado das POCs (se houver)
- Matriz de riscos técnicos
- Estimativa detalhada de esforço'''
            },
            {
                'ordem': 5,
                'titulo': 'Definição de Escopo e Cronograma',
                'tempo_estimado': 240,
                'descricao': '''OBJETIVO: Definir escopo fechado e cronograma realista.

ATIVIDADES:

1. DEFINIÇÃO DO MVP (Minimum Viable Product)
   - Selecionar funcionalidades essenciais
   - Definir o que fica para fases futuras
   - Validar MVP com stakeholders

2. CRIAÇÃO DO WBS (Work Breakdown Structure)
   - Quebrar projeto em fases
   - Quebrar fases em entregas
   - Quebrar entregas em tarefas

3. ESTIMATIVAS
   - Planning Poker com equipe
   - Considerar dependências
   - Incluir tempo para testes
   - Incluir tempo para correções

4. CRONOGRAMA
   - Definir marcos (milestones)
   - Identificar caminho crítico
   - Alocar recursos
   - Definir entregas parciais

5. APROVAÇÃO
   - Apresentar para stakeholders
   - Documentar premissas
   - Obter aprovação formal

ENTREGÁVEIS:
- Documento de escopo aprovado
- WBS detalhado
- Cronograma do projeto
- Termo de aceite do escopo

IMPORTANTE:
- Scope creep é o maior inimigo - documente TUDO
- Qualquer mudança deve passar por change request'''
            },

            # =====================================
            # FASE 2: ARQUITETURA E DESIGN
            # =====================================
            {
                'ordem': 6,
                'titulo': 'Definição da Arquitetura do Sistema',
                'tempo_estimado': 480,
                'descricao': '''OBJETIVO: Definir a arquitetura técnica que suportará o sistema.

DECISÕES ARQUITETURAIS:

1. PADRÃO ARQUITETURAL
   - Monolito vs Microserviços
   - MVC, Clean Architecture, Hexagonal
   - Event-Driven, CQRS

2. STACK TECNOLÓGICA
   Backend:
   - Linguagem (Python, Node, Java, Go, etc)
   - Framework (Django, FastAPI, Spring, etc)
   - ORM/Query Builder

   Frontend:
   - Framework (React, Vue, Angular, etc)
   - State Management
   - CSS Framework

   Mobile (se aplicável):
   - Nativo vs Cross-platform
   - React Native, Flutter, etc

3. BANCO DE DADOS
   - Relacional vs NoSQL vs Híbrido
   - PostgreSQL, MySQL, MongoDB, Redis
   - Estratégia de cache

4. INFRAESTRUTURA
   - Cloud provider (AWS, GCP, Azure)
   - Containers (Docker, Kubernetes)
   - CI/CD pipeline
   - Monitoramento

5. INTEGRAÇÕES
   - APIs internas
   - APIs externas
   - Mensageria (RabbitMQ, Kafka)
   - Webhooks

ENTREGÁVEIS:
- Documento de Arquitetura de Software (DAS)
- Diagrama de arquitetura (C4 Model)
- ADRs (Architecture Decision Records)
- Stack tecnológica definida'''
            },
            {
                'ordem': 7,
                'titulo': 'Modelagem de Dados',
                'tempo_estimado': 360,
                'descricao': '''OBJETIVO: Projetar o modelo de dados que suportará o sistema.

ATIVIDADES:

1. MODELO CONCEITUAL
   - Identificar entidades principais
   - Mapear relacionamentos
   - Diagrama ER conceitual

2. MODELO LÓGICO
   - Definir atributos de cada entidade
   - Normalização (até 3FN)
   - Definir chaves primárias e estrangeiras
   - Identificar índices necessários

3. MODELO FÍSICO
   - Tipos de dados específicos do SGBD
   - Constraints (NOT NULL, UNIQUE, CHECK)
   - Particionamento (se necessário)
   - Estratégia de soft delete

4. DICIONÁRIO DE DADOS
   - Documentar cada tabela
   - Documentar cada campo
   - Regras de validação
   - Valores permitidos (enums)

BOAS PRÁTICAS:
- Use snake_case para nomes
- Prefixe tabelas por módulo
- created_at e updated_at em todas as tabelas
- Soft delete (deleted_at) quando apropriado
- UUIDs para IDs públicos

ENTREGÁVEIS:
- Diagrama ER completo
- Dicionário de dados
- Scripts de criação (migrations)
- Dados de seed/fixtures'''
            },
            {
                'ordem': 8,
                'titulo': 'Design de APIs',
                'tempo_estimado': 300,
                'descricao': '''OBJETIVO: Projetar as APIs do sistema seguindo boas práticas.

PADRÕES REST:

1. NOMENCLATURA
   - Recursos no plural: /users, /orders
   - Verbos HTTP corretos:
     GET = Leitura
     POST = Criação
     PUT = Atualização completa
     PATCH = Atualização parcial
     DELETE = Remoção

2. ESTRUTURA DE ENDPOINTS
   GET    /recursos          - Listar
   GET    /recursos/:id      - Detalhe
   POST   /recursos          - Criar
   PUT    /recursos/:id      - Atualizar
   DELETE /recursos/:id      - Remover

   Relacionamentos:
   GET /usuarios/:id/pedidos - Pedidos do usuário

3. QUERY PARAMETERS
   - Paginação: ?page=1&per_page=20
   - Ordenação: ?sort=created_at&order=desc
   - Filtros: ?status=active&type=premium
   - Busca: ?q=termo

4. RESPOSTAS
   - 200 OK - Sucesso
   - 201 Created - Criado
   - 204 No Content - Sucesso sem corpo
   - 400 Bad Request - Erro de validação
   - 401 Unauthorized - Não autenticado
   - 403 Forbidden - Sem permissão
   - 404 Not Found - Não encontrado
   - 422 Unprocessable Entity - Erro de negócio
   - 500 Internal Error - Erro do servidor

5. FORMATO DE RESPOSTA
```json
{
  "data": {...},
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100
  }
}
```

ENTREGÁVEIS:
- Documentação OpenAPI/Swagger
- Collection do Postman/Insomnia
- Exemplos de request/response'''
            },
            {
                'ordem': 9,
                'titulo': 'Design de Interface (UI/UX)',
                'tempo_estimado': 480,
                'descricao': '''OBJETIVO: Criar a interface do usuário com boa experiência.

PROCESSO:

1. PESQUISA DE USUÁRIO
   - Personas definidas
   - Jornadas de usuário
   - Análise de concorrentes

2. ARQUITETURA DE INFORMAÇÃO
   - Mapa do site/aplicativo
   - Hierarquia de navegação
   - Nomenclatura consistente

3. WIREFRAMES (Baixa fidelidade)
   - Esboços das telas principais
   - Fluxos de navegação
   - Validação com stakeholders

4. DESIGN SYSTEM
   - Paleta de cores
   - Tipografia
   - Componentes base (botões, inputs, cards)
   - Espaçamentos e grid
   - Ícones

5. PROTÓTIPO (Alta fidelidade)
   - Telas finais no Figma/Sketch
   - Interações e animações
   - Estados (loading, erro, vazio)
   - Responsividade

6. ACESSIBILIDADE
   - Contraste de cores (WCAG)
   - Tamanho de fonte adequado
   - Navegação por teclado
   - Labels para screen readers

ENTREGÁVEIS:
- Wireframes aprovados
- Design System documentado
- Protótipo navegável
- Assets para desenvolvimento
- Guia de estilos'''
            },

            # =====================================
            # FASE 3: SETUP E CONFIGURAÇÃO
            # =====================================
            {
                'ordem': 10,
                'titulo': 'Setup do Ambiente de Desenvolvimento',
                'tempo_estimado': 240,
                'descricao': '''OBJETIVO: Configurar ambiente de desenvolvimento padronizado.

ATIVIDADES:

1. REPOSITÓRIO
   - Criar repositório Git
   - Configurar branches (main, develop, feature/*)
   - Definir estratégia de branching (GitFlow, Trunk-based)
   - Configurar proteção de branches
   - Template de PR

2. PROJETO BASE
   - Estrutura de pastas
   - Configurações iniciais
   - Variáveis de ambiente (.env.example)
   - Docker Compose para desenvolvimento

3. QUALIDADE DE CÓDIGO
   - Linter configurado (ESLint, Flake8, etc)
   - Formatter (Prettier, Black)
   - Pre-commit hooks
   - EditorConfig

4. DOCUMENTAÇÃO INICIAL
   - README.md completo
   - CONTRIBUTING.md
   - Instruções de setup local

5. FERRAMENTAS
   - Issue tracker (GitHub Issues, Jira)
   - Board de tarefas (Kanban)
   - Comunicação (Slack channel)

ESTRUTURA EXEMPLO (Python/Django):
```
projeto/
├── apps/
│   ├── core/
│   ├── users/
│   └── ...
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── docs/
├── scripts/
├── tests/
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── README.md
└── requirements/
    ├── base.txt
    ├── local.txt
    └── production.txt
```

ENTREGÁVEIS:
- Repositório configurado
- Ambiente Docker funcional
- Documentação de setup'''
            },
            {
                'ordem': 11,
                'titulo': 'Configuração de CI/CD',
                'tempo_estimado': 300,
                'descricao': '''OBJETIVO: Automatizar build, testes e deploy.

PIPELINE CI (Continuous Integration):

1. TRIGGER
   - Push em branches
   - Pull Requests

2. STAGES
   a) Checkout código
   b) Instalar dependências
   c) Rodar linter
   d) Rodar testes unitários
   e) Rodar testes de integração
   f) Análise de cobertura
   g) Build da aplicação
   h) Build da imagem Docker
   i) Push para registry

PIPELINE CD (Continuous Deployment):

1. AMBIENTES
   - Development (automático em develop)
   - Staging (automático em release/*)
   - Production (manual com aprovação)

2. ESTRATÉGIA DE DEPLOY
   - Blue/Green deployment
   - Canary releases
   - Rolling updates

EXEMPLO GITHUB ACTIONS:
```yaml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: ./deploy.sh
```

ENTREGÁVEIS:
- Pipeline CI configurado
- Pipeline CD configurado
- Ambientes criados (dev, staging, prod)
- Documentação de deploy'''
            },
            {
                'ordem': 12,
                'titulo': 'Setup de Infraestrutura',
                'tempo_estimado': 360,
                'descricao': '''OBJETIVO: Provisionar infraestrutura necessária.

CHECKLIST INFRAESTRUTURA:

1. SERVIDORES/CONTAINERS
   - [ ] Cluster Kubernetes ou servidores
   - [ ] Load balancer configurado
   - [ ] Auto-scaling definido
   - [ ] Health checks

2. BANCO DE DADOS
   - [ ] Instância criada
   - [ ] Backups automáticos
   - [ ] Réplicas (se necessário)
   - [ ] Conexão segura (SSL)

3. CACHE
   - [ ] Redis/Memcached
   - [ ] Política de expiração

4. ARMAZENAMENTO
   - [ ] S3/Blob storage para arquivos
   - [ ] CDN para assets estáticos
   - [ ] Política de lifecycle

5. REDE
   - [ ] VPC configurada
   - [ ] Security groups
   - [ ] DNS configurado
   - [ ] Certificado SSL

6. MONITORAMENTO
   - [ ] APM (New Relic, Datadog)
   - [ ] Logs centralizados
   - [ ] Alertas configurados
   - [ ] Dashboards

7. SEGURANÇA
   - [ ] WAF
   - [ ] DDoS protection
   - [ ] Secrets management
   - [ ] Audit logs

INFRAESTRUTURA COMO CÓDIGO:
- Terraform para provisionamento
- Ansible para configuração
- Helm charts para Kubernetes

ENTREGÁVEIS:
- Infraestrutura provisionada
- IaC versionado
- Documentação de arquitetura
- Runbooks operacionais'''
            },

            # =====================================
            # FASE 4: DESENVOLVIMENTO
            # =====================================
            {
                'ordem': 13,
                'titulo': 'Desenvolvimento do Core/Base',
                'tempo_estimado': 480,
                'descricao': '''OBJETIVO: Desenvolver a estrutura base do sistema.

COMPONENTES BASE:

1. AUTENTICAÇÃO E AUTORIZAÇÃO
   - Login/Logout
   - Registro de usuários
   - Recuperação de senha
   - JWT/Session management
   - Refresh tokens
   - Permissões e roles

2. USUÁRIOS E PERFIS
   - CRUD de usuários
   - Perfis de acesso
   - Configurações do usuário

3. MIDDLEWARE
   - Autenticação
   - Logging de requisições
   - Rate limiting
   - CORS
   - Compressão

4. UTILITÁRIOS
   - Paginação genérica
   - Filtros e ordenação
   - Upload de arquivos
   - Envio de emails
   - Geração de PDFs

5. TRATAMENTO DE ERROS
   - Exception handlers
   - Logging estruturado
   - Respostas padronizadas

PADRÕES DE CÓDIGO:
- Classes/funções pequenas (max 50 linhas)
- Nomes descritivos
- Comentários quando necessário
- Type hints (Python) / TypeScript
- Testes para cada funcionalidade

ENTREGÁVEIS:
- Módulo de autenticação
- CRUD de usuários
- Middleware configurado
- Testes do core'''
            },
            {
                'ordem': 14,
                'titulo': 'Desenvolvimento dos Módulos de Negócio',
                'tempo_estimado': 960,
                'descricao': '''OBJETIVO: Desenvolver as funcionalidades específicas do negócio.

PROCESSO POR FUNCIONALIDADE:

1. ANÁLISE
   - Revisar user story
   - Entender regras de negócio
   - Identificar dependências

2. DESIGN
   - Modelar dados (se novo)
   - Definir endpoints (se API)
   - Desenhar fluxo

3. IMPLEMENTAÇÃO
   - Model/Entity
   - Repository/DAO
   - Service/UseCase
   - Controller/View
   - Validações

4. TESTES
   - Testes unitários
   - Testes de integração
   - Testar casos de erro

5. CODE REVIEW
   - PR com descrição clara
   - Screenshots (se UI)
   - Checklist de review

BOAS PRÁTICAS:
- Uma PR por funcionalidade
- Commits atômicos e descritivos
- Não deixar TODO no código
- Documentar decisões técnicas

EXEMPLO DE COMMIT:
```
feat(orders): add order creation endpoint

- Create Order model with validations
- Implement OrderService with business rules
- Add POST /orders endpoint
- Add tests for happy path and errors

Closes #123
```

ENTREGÁVEIS:
- Módulos desenvolvidos
- Testes passando
- PRs revisados e mergeados
- Documentação atualizada'''
            },
            {
                'ordem': 15,
                'titulo': 'Desenvolvimento do Frontend',
                'tempo_estimado': 720,
                'descricao': '''OBJETIVO: Desenvolver a interface do usuário.

COMPONENTES:

1. ESTRUTURA BASE
   - Setup do projeto (Vite, CRA, Next)
   - Rotas configuradas
   - Layout principal
   - Componentes base

2. AUTENTICAÇÃO
   - Tela de login
   - Tela de registro
   - Recuperação de senha
   - Proteção de rotas

3. COMPONENTES REUTILIZÁVEIS
   - Botões, inputs, selects
   - Modais e alertas
   - Tabelas com paginação
   - Cards e listas
   - Loading states

4. PÁGINAS
   - Dashboard
   - CRUD de entidades
   - Relatórios
   - Configurações

5. INTEGRAÇÃO COM API
   - Cliente HTTP configurado
   - Interceptors (auth, errors)
   - Cache de dados (React Query, SWR)
   - Loading e error states

6. RESPONSIVIDADE
   - Mobile first
   - Breakpoints consistentes
   - Navegação mobile

CHECKLIST POR TELA:
- [ ] Layout conforme design
- [ ] Responsivo
- [ ] Loading states
- [ ] Error states
- [ ] Empty states
- [ ] Validações de formulário
- [ ] Acessibilidade básica
- [ ] Testes

ENTREGÁVEIS:
- Frontend funcional
- Integrado com backend
- Responsivo
- Testes E2E principais'''
            },
            {
                'ordem': 16,
                'titulo': 'Integrações com Sistemas Externos',
                'tempo_estimado': 480,
                'descricao': '''OBJETIVO: Implementar integrações com APIs e sistemas externos.

PROCESSO DE INTEGRAÇÃO:

1. ANÁLISE
   - Documentação da API externa
   - Autenticação necessária
   - Rate limits
   - Webhooks disponíveis

2. IMPLEMENTAÇÃO
   - Cliente HTTP dedicado
   - Retry com backoff exponencial
   - Circuit breaker
   - Logging de chamadas

3. TRATAMENTO DE ERROS
   - Timeout adequado
   - Fallback quando possível
   - Alertas para falhas

4. TESTES
   - Mocks para testes
   - Testes de contrato
   - Testes de resiliência

PADRÃO DE CLIENTE:
```python
class ExternalAPIClient:
    def __init__(self):
        self.base_url = settings.EXTERNAL_API_URL
        self.timeout = 30
        self.max_retries = 3

    @retry(max_attempts=3, backoff=2)
    def get_data(self, id):
        try:
            response = requests.get(
                f"{self.base_url}/data/{id}",
                timeout=self.timeout,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"External API error: {e}")
            raise IntegrationError(str(e))
```

INTEGRAÇÕES COMUNS:
- Gateway de pagamento
- Serviços de email
- SMS/WhatsApp
- Storage (S3)
- Autenticação externa (OAuth)

ENTREGÁVEIS:
- Clientes de integração
- Documentação das integrações
- Testes de integração
- Monitoramento configurado'''
            },

            # =====================================
            # FASE 5: QUALIDADE E TESTES
            # =====================================
            {
                'ordem': 17,
                'titulo': 'Testes Unitários',
                'tempo_estimado': 360,
                'descricao': '''OBJETIVO: Garantir qualidade através de testes unitários.

COBERTURA MÍNIMA: 80%

O QUE TESTAR:
1. Funções de negócio
2. Validações
3. Cálculos
4. Transformações de dados
5. Edge cases

ESTRUTURA DE TESTE (AAA):
```python
def test_calculate_discount():
    # Arrange (preparar)
    order = Order(total=100)
    coupon = Coupon(discount_percent=10)

    # Act (agir)
    result = calculate_discount(order, coupon)

    # Assert (verificar)
    assert result == 10
```

BOAS PRÁTICAS:
- Um assert por teste (quando possível)
- Nomes descritivos
- Testar casos de sucesso E erro
- Não testar implementação, testar comportamento
- Mocks para dependências externas

FERRAMENTAS:
- Python: pytest, unittest
- JavaScript: Jest, Vitest
- Mocking: unittest.mock, jest.mock

EXEMPLO DE ORGANIZAÇÃO:
```
tests/
├── unit/
│   ├── test_order_service.py
│   ├── test_payment_calculator.py
│   └── test_validators.py
├── integration/
│   └── test_api_orders.py
└── conftest.py (fixtures)
```

ENTREGÁVEIS:
- Testes unitários para services
- Testes unitários para utils
- Cobertura > 80%
- CI rodando testes'''
            },
            {
                'ordem': 18,
                'titulo': 'Testes de Integração',
                'tempo_estimado': 300,
                'descricao': '''OBJETIVO: Testar a integração entre componentes.

O QUE TESTAR:
1. Endpoints da API
2. Fluxos completos
3. Integração com banco de dados
4. Integrações externas (com mocks)

TESTE DE API:
```python
class TestOrderAPI:
    def test_create_order_success(self, client, auth_headers):
        payload = {
            "items": [{"product_id": 1, "quantity": 2}],
            "address_id": 1
        }

        response = client.post(
            "/api/orders/",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["status"] == "pending"

    def test_create_order_empty_cart(self, client, auth_headers):
        response = client.post(
            "/api/orders/",
            json={"items": []},
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "items" in response.json()["errors"]
```

FIXTURES:
- Banco de dados limpo por teste
- Dados de teste consistentes
- Usuários de teste

CENÁRIOS:
- Happy path
- Validação de entrada
- Autenticação/Autorização
- Erros de negócio
- Erros de sistema

ENTREGÁVEIS:
- Testes de todos os endpoints
- Testes de fluxos críticos
- Fixtures organizadas
- CI com testes de integração'''
            },
            {
                'ordem': 19,
                'titulo': 'Testes E2E (End-to-End)',
                'tempo_estimado': 360,
                'descricao': '''OBJETIVO: Testar fluxos completos do ponto de vista do usuário.

FERRAMENTA RECOMENDADA: Playwright ou Cypress

FLUXOS CRÍTICOS A TESTAR:
1. Login/Logout
2. Cadastro de usuário
3. Fluxo principal de compra/uso
4. CRUD das entidades principais
5. Relatórios

ESTRUTURA DE TESTE:
```javascript
describe('Order Flow', () => {
  beforeEach(() => {
    cy.login('user@test.com', 'password')
  })

  it('should complete a purchase', () => {
    // Adicionar ao carrinho
    cy.visit('/products')
    cy.get('[data-testid="product-1"]').click()
    cy.get('[data-testid="add-to-cart"]').click()

    // Checkout
    cy.get('[data-testid="cart-icon"]').click()
    cy.get('[data-testid="checkout-btn"]').click()

    // Pagamento
    cy.get('[data-testid="card-number"]').type('4111111111111111')
    cy.get('[data-testid="pay-btn"]').click()

    // Confirmação
    cy.url().should('include', '/order-confirmation')
    cy.contains('Pedido realizado com sucesso')
  })
})
```

BOAS PRÁTICAS:
- Usar data-testid para seletores
- Não depender de textos (podem mudar)
- Testes independentes
- Setup/Teardown adequado
- Screenshots em falha

ENTREGÁVEIS:
- Testes E2E dos fluxos críticos
- CI rodando E2E
- Relatório de execução
- Screenshots de falhas'''
            },
            {
                'ordem': 20,
                'titulo': 'Testes de Performance',
                'tempo_estimado': 300,
                'descricao': '''OBJETIVO: Garantir que o sistema suporta a carga esperada.

FERRAMENTAS:
- k6, Locust, JMeter, Artillery

TIPOS DE TESTE:

1. LOAD TEST
   - Carga normal esperada
   - Verificar tempo de resposta
   - Verificar throughput

2. STRESS TEST
   - Aumentar carga gradualmente
   - Encontrar ponto de quebra
   - Verificar recuperação

3. SPIKE TEST
   - Pico repentino de carga
   - Verificar comportamento

4. SOAK TEST
   - Carga constante por longo período
   - Identificar memory leaks

EXEMPLO K6:
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // ramp up
    { duration: '5m', target: 100 },  // stay
    { duration: '2m', target: 0 },    // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% < 500ms
    http_req_failed: ['rate<0.01'],    // < 1% errors
  },
};

export default function () {
  const res = http.get('https://api.example.com/products');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

MÉTRICAS A COLETAR:
- Tempo de resposta (p50, p95, p99)
- Throughput (req/s)
- Taxa de erro
- Uso de CPU/memória
- Conexões de banco

ENTREGÁVEIS:
- Scripts de teste de carga
- Relatório de performance
- Baseline estabelecido
- Otimizações identificadas'''
            },

            # =====================================
            # FASE 6: SEGURANÇA
            # =====================================
            {
                'ordem': 21,
                'titulo': 'Análise de Segurança (OWASP Top 10)',
                'tempo_estimado': 480,
                'descricao': '''OBJETIVO: Identificar e corrigir vulnerabilidades de segurança.

OWASP TOP 10 - CHECKLIST:

1. INJECTION (SQL, NoSQL, LDAP)
   - [ ] Usar queries parametrizadas/ORM
   - [ ] Validar e sanitizar inputs
   - [ ] Escapar outputs

2. BROKEN AUTHENTICATION
   - [ ] Senhas com hash seguro (bcrypt, argon2)
   - [ ] Rate limiting em login
   - [ ] Session timeout
   - [ ] Invalidar sessões no logout

3. SENSITIVE DATA EXPOSURE
   - [ ] HTTPS obrigatório
   - [ ] Dados sensíveis criptografados
   - [ ] Não expor dados em logs
   - [ ] Mascarar dados sensíveis

4. XML EXTERNAL ENTITIES (XXE)
   - [ ] Desabilitar DTD em parsers XML
   - [ ] Usar JSON quando possível

5. BROKEN ACCESS CONTROL
   - [ ] Verificar permissões em cada request
   - [ ] Não confiar em dados do cliente
   - [ ] Impedir IDOR (Insecure Direct Object Reference)

6. SECURITY MISCONFIGURATION
   - [ ] Remover headers desnecessários
   - [ ] Desabilitar debug em produção
   - [ ] Atualizar dependências

7. CROSS-SITE SCRIPTING (XSS)
   - [ ] Escapar output HTML
   - [ ] Content Security Policy
   - [ ] HttpOnly cookies

8. INSECURE DESERIALIZATION
   - [ ] Não deserializar dados não confiáveis
   - [ ] Validar antes de deserializar

9. USING COMPONENTS WITH KNOWN VULNERABILITIES
   - [ ] Audit de dependências
   - [ ] Atualizar regularmente
   - [ ] Monitorar CVEs

10. INSUFFICIENT LOGGING & MONITORING
    - [ ] Logar tentativas de login falhas
    - [ ] Logar acessos a dados sensíveis
    - [ ] Alertas para anomalias

FERRAMENTAS:
- SAST: SonarQube, Bandit, ESLint security
- DAST: OWASP ZAP, Burp Suite
- Dependency check: Snyk, npm audit, pip-audit

ENTREGÁVEIS:
- Relatório de vulnerabilidades
- Correções implementadas
- Scan de segurança no CI'''
            },
            {
                'ordem': 22,
                'titulo': 'Implementação de Segurança',
                'tempo_estimado': 360,
                'descricao': '''OBJETIVO: Implementar controles de segurança no sistema.

AUTENTICAÇÃO:
```python
# Configuração segura de senha
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
]

# JWT seguro
JWT_SETTINGS = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

HEADERS DE SEGURANÇA:
```python
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# CSP
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
```

RATE LIMITING:
```python
# Django Ratelimit
@ratelimit(key='ip', rate='5/m', method='POST')
def login_view(request):
    ...

# API throttling
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/minute',
    }
}
```

AUDITORIA:
```python
class AuditLogMiddleware:
    def process_request(self, request):
        if request.user.is_authenticated:
            AuditLog.objects.create(
                user=request.user,
                action=request.method,
                path=request.path,
                ip=get_client_ip(request),
                timestamp=timezone.now()
            )
```

ENTREGÁVEIS:
- Autenticação robusta
- Headers de segurança
- Rate limiting
- Auditoria implementada
- Secrets management'''
            },
            {
                'ordem': 23,
                'titulo': 'LGPD e Compliance',
                'tempo_estimado': 300,
                'descricao': '''OBJETIVO: Garantir conformidade com LGPD e regulamentações.

REQUISITOS LGPD:

1. CONSENTIMENTO
   - [ ] Coletar consentimento explícito
   - [ ] Documentar finalidade do tratamento
   - [ ] Permitir revogação do consentimento

2. DIREITOS DO TITULAR
   - [ ] Acesso aos dados pessoais
   - [ ] Correção de dados incorretos
   - [ ] Exclusão de dados (direito ao esquecimento)
   - [ ] Portabilidade de dados
   - [ ] Informação sobre compartilhamento

3. MINIMIZAÇÃO DE DADOS
   - [ ] Coletar apenas dados necessários
   - [ ] Definir período de retenção
   - [ ] Anonimização/pseudonimização

4. SEGURANÇA
   - [ ] Criptografia de dados sensíveis
   - [ ] Controle de acesso
   - [ ] Logs de acesso a dados pessoais

5. DOCUMENTAÇÃO
   - [ ] Política de privacidade
   - [ ] Termos de uso
   - [ ] Registro de atividades de tratamento
   - [ ] Relatório de impacto (RIPD)

IMPLEMENTAÇÃO:
```python
class DataExportView(APIView):
    """Exportar dados do usuário (portabilidade)"""
    def get(self, request):
        user = request.user
        data = {
            'personal_info': UserSerializer(user).data,
            'orders': OrderSerializer(user.orders.all(), many=True).data,
            'preferences': PreferencesSerializer(user.preferences).data,
        }
        return Response(data)

class DataDeletionView(APIView):
    """Excluir dados do usuário (direito ao esquecimento)"""
    def delete(self, request):
        user = request.user
        # Anonimizar ao invés de deletar (manter integridade)
        user.email = f"deleted_{user.id}@anonymized.local"
        user.name = "Usuário Removido"
        user.phone = None
        user.is_active = False
        user.save()
        return Response(status=204)
```

ENTREGÁVEIS:
- Funcionalidades LGPD implementadas
- Políticas documentadas
- Consent management
- Processo de exclusão de dados'''
            },

            # =====================================
            # FASE 7: DEPLOY E GO-LIVE
            # =====================================
            {
                'ordem': 24,
                'titulo': 'Preparação para Deploy',
                'tempo_estimado': 240,
                'descricao': '''OBJETIVO: Preparar o sistema para ir para produção.

CHECKLIST PRÉ-DEPLOY:

1. CÓDIGO
   - [ ] Todas as features no branch main
   - [ ] Code review completo
   - [ ] Sem débitos técnicos críticos
   - [ ] TODOs resolvidos

2. TESTES
   - [ ] Todos os testes passando
   - [ ] Cobertura adequada
   - [ ] Testes de regressão ok
   - [ ] Testes de carga ok

3. CONFIGURAÇÃO
   - [ ] Variáveis de ambiente documentadas
   - [ ] Secrets configurados
   - [ ] Domínios/DNS configurados
   - [ ] SSL/TLS certificados

4. BANCO DE DADOS
   - [ ] Migrations testadas
   - [ ] Dados de seed preparados
   - [ ] Backup configurado
   - [ ] Rollback testado

5. MONITORAMENTO
   - [ ] APM configurado
   - [ ] Logs centralizados
   - [ ] Alertas definidos
   - [ ] Dashboards criados

6. DOCUMENTAÇÃO
   - [ ] Manual do usuário
   - [ ] Documentação técnica
   - [ ] Runbooks operacionais
   - [ ] FAQ/Troubleshooting

7. PLANO DE ROLLBACK
   - [ ] Procedimento documentado
   - [ ] Testado em staging
   - [ ] Tempo estimado de rollback

ENTREGÁVEIS:
- Checklist completo
- Documentação atualizada
- Plano de rollback
- Aprovação para deploy'''
            },
            {
                'ordem': 25,
                'titulo': 'Deploy em Produção',
                'tempo_estimado': 180,
                'descricao': '''OBJETIVO: Realizar o deploy em ambiente de produção.

PROCEDIMENTO DE DEPLOY:

1. PRÉ-DEPLOY
   - Comunicar equipe sobre deploy
   - Verificar janela de manutenção
   - Backup do banco de dados
   - Preparar monitoramento

2. DEPLOY
   a) Ativar página de manutenção (se necessário)
   b) Executar migrations
   c) Deploy da aplicação
   d) Verificar health checks
   e) Executar smoke tests
   f) Desativar página de manutenção

3. PÓS-DEPLOY
   - Monitorar logs
   - Verificar métricas
   - Testar fluxos críticos
   - Comunicar sucesso

COMANDOS EXEMPLO:
```bash
# Backup
pg_dump -h host -U user dbname > backup_$(date +%Y%m%d_%H%M%S).sql

# Deploy
kubectl set image deployment/app app=image:v1.2.3

# Verificar
kubectl rollout status deployment/app

# Rollback (se necessário)
kubectl rollout undo deployment/app
```

SMOKE TESTS:
- [ ] Página inicial carrega
- [ ] Login funciona
- [ ] API responde
- [ ] Fluxo principal ok

CRITÉRIOS DE SUCESSO:
- Zero erros 500 nos primeiros 30 minutos
- Tempo de resposta dentro do esperado
- Todas as funcionalidades acessíveis

ENTREGÁVEIS:
- Deploy realizado
- Logs do deploy
- Evidências de testes
- Comunicado de sucesso'''
            },
            {
                'ordem': 26,
                'titulo': 'Treinamento de Usuários',
                'tempo_estimado': 360,
                'descricao': '''OBJETIVO: Capacitar usuários para usar o sistema.

CONTEÚDO DO TREINAMENTO:

1. VISÃO GERAL
   - Objetivo do sistema
   - Principais funcionalidades
   - Navegação básica

2. POR PERFIL DE USUÁRIO
   - Funcionalidades específicas
   - Fluxos de trabalho
   - Permissões e limitações

3. CASOS DE USO
   - Demonstração prática
   - Exercícios guiados
   - Resolução de dúvidas

4. SUPORTE
   - Como reportar problemas
   - FAQ
   - Contatos de suporte

MATERIAIS:

1. DOCUMENTAÇÃO
   - Manual do usuário (PDF)
   - Guias rápidos (1 página)
   - FAQ

2. VÍDEOS
   - Tutoriais por funcionalidade
   - Gravação do treinamento

3. AMBIENTE DE TREINO
   - Sandbox para prática
   - Dados de exemplo

CRONOGRAMA:
- Sessão 1: Visão geral (1h)
- Sessão 2: Funcionalidades principais (2h)
- Sessão 3: Prática guiada (2h)
- Sessão 4: Dúvidas e casos especiais (1h)

ENTREGÁVEIS:
- Treinamentos realizados
- Materiais de apoio
- Lista de participantes
- Avaliação de satisfação'''
            },

            # =====================================
            # FASE 8: PÓS-GO-LIVE
            # =====================================
            {
                'ordem': 27,
                'titulo': 'Monitoramento Pós-Deploy',
                'tempo_estimado': 240,
                'descricao': '''OBJETIVO: Acompanhar o sistema nas primeiras semanas em produção.

PERÍODO: 2 semanas após go-live

ATIVIDADES DIÁRIAS:

1. VERIFICAÇÃO DE SAÚDE
   - Verificar dashboards
   - Revisar logs de erro
   - Checar alertas disparados
   - Verificar performance

2. ATENDIMENTO
   - Responder tickets de suporte
   - Escalar problemas críticos
   - Documentar issues recorrentes

3. CORREÇÕES RÁPIDAS
   - Hotfixes para bugs críticos
   - Ajustes de configuração
   - Otimizações emergenciais

MÉTRICAS A MONITORAR:
- Taxa de erro (< 1%)
- Tempo de resposta (p95 < 2s)
- Disponibilidade (> 99.9%)
- Uso de recursos (CPU, memória)
- Taxa de conversão/uso de features

REUNIÃO DIÁRIA (stand-up):
- Incidentes das últimas 24h
- Tickets de suporte
- Ações necessárias
- Bloqueios

ESCALONAMENTO:
- P1 (Crítico): Sistema fora do ar - resposta imediata
- P2 (Alto): Funcionalidade crítica com defeito - 4h
- P3 (Médio): Bug que afeta uso - 24h
- P4 (Baixo): Melhorias/ajustes - próxima sprint

ENTREGÁVEIS:
- Relatórios diários
- Lista de bugs encontrados
- Melhorias identificadas
- Feedback dos usuários'''
            },
            {
                'ordem': 28,
                'titulo': 'Correções e Ajustes Pós-Deploy',
                'tempo_estimado': 480,
                'descricao': '''OBJETIVO: Corrigir bugs e fazer ajustes identificados após o go-live.

PROCESSO:

1. TRIAGEM
   - Classificar por severidade
   - Identificar causa raiz
   - Estimar esforço

2. PRIORIZAÇÃO
   - Bugs críticos primeiro
   - Quick wins (alto valor, baixo esforço)
   - Débitos técnicos urgentes

3. CORREÇÃO
   - Desenvolver fix
   - Testar localmente
   - Code review
   - Deploy

4. VALIDAÇÃO
   - Verificar em produção
   - Comunicar usuário
   - Fechar ticket

TIPOS DE AJUSTES:

1. BUGS
   - Erros de lógica
   - Problemas de UI
   - Integrações falhando

2. PERFORMANCE
   - Queries lentas
   - Cache inadequado
   - Memory leaks

3. USABILIDADE
   - Fluxos confusos
   - Textos incorretos
   - Falta de feedback

4. SEGURANÇA
   - Vulnerabilidades encontradas
   - Permissões incorretas

ENTREGÁVEIS:
- Bugs corrigidos
- Relatório de issues
- Melhorias de performance
- Feedback implementado'''
            },
            {
                'ordem': 29,
                'titulo': 'Documentação Final',
                'tempo_estimado': 360,
                'descricao': '''OBJETIVO: Consolidar toda a documentação do projeto.

DOCUMENTAÇÃO TÉCNICA:

1. ARQUITETURA
   - Diagrama de arquitetura atualizado
   - Decisões arquiteturais (ADRs)
   - Fluxo de dados

2. API
   - Documentação OpenAPI completa
   - Exemplos de uso
   - Postman collection

3. BANCO DE DADOS
   - Diagrama ER atualizado
   - Dicionário de dados
   - Procedures/triggers

4. INFRAESTRUTURA
   - Diagrama de infra
   - Configurações
   - Runbooks

5. CÓDIGO
   - README atualizado
   - Guia de contribuição
   - Changelog

DOCUMENTAÇÃO DO USUÁRIO:

1. MANUAL
   - Guia completo por funcionalidade
   - Screenshots atualizados
   - Troubleshooting

2. TUTORIAIS
   - Vídeos gravados
   - Guias passo-a-passo

3. FAQ
   - Perguntas frequentes
   - Soluções comuns

ONDE MANTER:
- Código: README, docs/ no repositório
- API: Swagger/Redoc
- Wiki: Confluence, Notion, GitBook
- Vídeos: YouTube privado, Loom

ENTREGÁVEIS:
- Documentação técnica completa
- Manual do usuário
- Wiki atualizada
- Vídeos tutoriais'''
            },
            {
                'ordem': 30,
                'titulo': 'Retrospectiva e Lições Aprendidas',
                'tempo_estimado': 180,
                'descricao': '''OBJETIVO: Refletir sobre o projeto e documentar aprendizados.

FORMATO DA RETROSPECTIVA:

1. O QUE FOI BEM
   - Práticas que funcionaram
   - Tecnologias acertadas
   - Processos eficientes
   - Comunicação positiva

2. O QUE PODE MELHORAR
   - Problemas enfrentados
   - Atrasos e causas
   - Gaps de comunicação
   - Dificuldades técnicas

3. AÇÕES PARA PRÓXIMOS PROJETOS
   - Mudanças de processo
   - Ferramentas a adotar
   - Treinamentos necessários
   - Templates a criar

MÉTRICAS DO PROJETO:
- Prazo planejado vs realizado
- Escopo planejado vs entregue
- Bugs em produção
- Satisfação do cliente
- Satisfação da equipe

PERGUNTAS PARA DISCUSSÃO:
- O que você faria diferente?
- Qual foi o maior desafio?
- Qual foi a maior conquista?
- O que devemos continuar fazendo?
- O que devemos parar de fazer?
- O que devemos começar a fazer?

TEMPLATE DE LIÇÕES APRENDIDAS:
```
Situação: [Descreva o contexto]
Problema: [O que aconteceu]
Causa: [Por que aconteceu]
Solução: [Como foi resolvido]
Lição: [O que aprendemos]
Ação: [O que faremos diferente]
```

ENTREGÁVEIS:
- Ata da retrospectiva
- Documento de lições aprendidas
- Plano de ação para melhorias
- Métricas finais do projeto'''
            },

            # =====================================
            # FASE 9: MANUTENÇÃO CONTÍNUA
            # =====================================
            {
                'ordem': 31,
                'titulo': 'Setup de Manutenção Contínua',
                'tempo_estimado': 240,
                'descricao': '''OBJETIVO: Estabelecer processos de manutenção do sistema.

PROCESSOS:

1. GESTÃO DE INCIDENTES
   - Canais de reporte
   - SLAs por severidade
   - Processo de escalonamento
   - Post-mortem para incidentes críticos

2. GESTÃO DE MUDANÇAS
   - Processo de change request
   - Aprovações necessárias
   - Janelas de manutenção
   - Comunicação de mudanças

3. ATUALIZAÇÕES
   - Política de atualização de dependências
   - Testes de regressão
   - Rollback procedure

4. BACKUP E RECOVERY
   - Frequência de backup
   - Teste de restore (mensal)
   - Disaster recovery plan

5. MONITORAMENTO
   - Dashboards de saúde
   - Alertas configurados
   - On-call rotation

CICLO DE RELEASE:
- Sprint de 2 semanas
- Release toda sexta-feira
- Hotfixes quando necessário

MÉTRICAS DE MANUTENÇÃO:
- MTTR (Mean Time To Recovery)
- MTBF (Mean Time Between Failures)
- Change failure rate
- Deployment frequency

ENTREGÁVEIS:
- Processos documentados
- SLAs definidos
- Calendário de manutenção
- Equipe de suporte definida'''
            },
            {
                'ordem': 32,
                'titulo': 'Planejamento de Evolução',
                'tempo_estimado': 180,
                'descricao': '''OBJETIVO: Planejar próximas fases e melhorias do sistema.

ROADMAP DE EVOLUÇÃO:

1. CURTO PRAZO (1-3 meses)
   - Correções pendentes
   - Melhorias de UX baseadas em feedback
   - Quick wins de performance
   - Débitos técnicos urgentes

2. MÉDIO PRAZO (3-6 meses)
   - Features que ficaram de fora do MVP
   - Integrações adicionais
   - Otimizações de escala
   - Novas automações

3. LONGO PRAZO (6-12 meses)
   - Novas funcionalidades estratégicas
   - Refatorações maiores
   - Modernização tecnológica
   - Expansão para novos mercados

FONTES DE INPUT:
- Feedback de usuários
- Análise de métricas de uso
- Tendências de mercado
- Requisitos regulatórios
- Melhorias técnicas

PRIORIZAÇÃO:
- Valor para o negócio
- Esforço de implementação
- Riscos técnicos
- Dependências

PROCESSO:
1. Coletar ideias continuamente
2. Revisar mensalmente
3. Priorizar trimestralmente
4. Planejar releases

ENTREGÁVEIS:
- Roadmap documentado
- Backlog priorizado
- Próximas releases planejadas
- Comunicação com stakeholders'''
            },
        ]

        for etapa_data in etapas:
            EtapaTemplate.objects.create(
                template=template,
                **etapa_data
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Template "{template.titulo}" criado com {len(etapas)} etapas!'
            )
        )
