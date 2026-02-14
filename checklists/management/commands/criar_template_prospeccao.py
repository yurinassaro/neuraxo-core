"""
Cria template completo de Prospecção Ativa.
Uso: python manage.py criar_template_prospeccao
"""
from django.core.management.base import BaseCommand
from checklists.models import ProjetoTemplate, EtapaTemplate


class Command(BaseCommand):
    help = 'Cria template de Prospecção Ativa completo'

    def handle(self, *args, **options):
        # Verificar se já existe
        if ProjetoTemplate.objects.filter(titulo__icontains='Prospecção Ativa').exists():
            self.stdout.write(self.style.WARNING('Template já existe. Pulando criação.'))
            return

        template = ProjetoTemplate.objects.create(
            titulo='Prospecção Ativa Completa',
            descricao='Template completo para projetos de prospecção ativa B2B. '
                      'Inclui todas as fases: definição de ICP, setup de ferramentas, '
                      'criação de listas, cadências multicanal (LinkedIn, Email, Telefone), '
                      'scripts, follow-ups e otimização. Baseado nas melhores práticas de 2025/2026.',
            cor='#dc2626',  # Vermelho
            ativo=True,
        )

        etapas = [
            # =====================================
            # FASE 1: ESTRATÉGIA E PLANEJAMENTO
            # =====================================
            {
                'ordem': 1,
                'titulo': 'Definição do ICP (Perfil de Cliente Ideal)',
                'tempo_estimado': 180,
                'descricao': '''OBJETIVO: Definir exatamente quem é o cliente ideal para focar os esforços.

SEM ICP CLARO = TIRO NO ESCURO

CRITÉRIOS PARA DEFINIR O ICP:

1. DADOS DEMOGRÁFICOS DA EMPRESA
   - Setor/Indústria (ex: SaaS, E-commerce, Indústria)
   - Tamanho (funcionários): 10-50, 50-200, 200-1000, 1000+
   - Faturamento anual estimado
   - Região geográfica
   - Tempo de mercado

2. DADOS DO DECISOR
   - Cargo (ex: CEO, Diretor de Marketing, Head de Vendas)
   - Nível hierárquico (C-level, Diretor, Gerente, Coordenador)
   - Área de atuação
   - Poder de decisão de compra

3. CARACTERÍSTICAS COMPORTAMENTAIS
   - Tecnologias que usa (stack)
   - Dores/problemas comuns
   - Objetivos de negócio
   - Objeções frequentes

4. SINAIS DE COMPRA (GATILHOS)
   - Empresa contratando
   - Recebeu investimento
   - Expandindo para nova região
   - Lançou produto novo
   - Trocou de liderança
   - Está crescendo rápido

TEMPLATE DE ICP:
```
EMPRESA IDEAL:
- Setor: _______________
- Tamanho: ___ a ___ funcionários
- Faturamento: R$ ___ a R$ ___
- Região: _______________
- Características: _______________

DECISOR IDEAL:
- Cargo: _______________
- Área: _______________
- Dores principais: _______________

GATILHOS DE COMPRA:
- _______________
- _______________

ANTI-ICP (quem NÃO queremos):
- _______________
- _______________
```

VALIDAÇÃO:
- Analise seus 10 melhores clientes atuais
- O que eles têm em comum?
- Por que compraram de você?
- Quanto tempo levou para fechar?

ENTREGÁVEIS:
- Documento de ICP completo
- Lista de gatilhos de compra
- Anti-ICP definido
- Validação com dados reais'''
            },
            {
                'ordem': 2,
                'titulo': 'Análise de Concorrência e Diferenciação',
                'tempo_estimado': 120,
                'descricao': '''OBJETIVO: Entender o cenário competitivo e definir seu diferencial.

O PROSPECT VAI COMPARAR VOCÊ COM:
- Concorrentes diretos
- Soluções alternativas
- Não fazer nada (status quo)

ANÁLISE DE CONCORRENTES:

1. IDENTIFICAR PRINCIPAIS CONCORRENTES
   - Quem aparece nas mesmas buscas?
   - Quem seus prospects mencionam?
   - Quem seus clientes usavam antes?

2. PARA CADA CONCORRENTE, MAPEAR:
   - Proposta de valor
   - Preço/modelo de negócio
   - Pontos fortes
   - Pontos fracos
   - Como se posicionam

3. SEU DIFERENCIAL
   - O que você faz que eles não fazem?
   - Por que clientes escolhem você?
   - Qual seu "unfair advantage"?

MATRIZ DE DIFERENCIAÇÃO:
```
| Critério        | Você | Conc. A | Conc. B |
|-----------------|------|---------|---------|
| Preço           |      |         |         |
| Suporte         |      |         |         |
| Funcionalidade X|      |         |         |
| Facilidade uso  |      |         |         |
| Tempo de setup  |      |         |         |
```

PITCH DE DIFERENCIAÇÃO (30 segundos):
```
"Diferente de [concorrente/alternativa] que [limitação],
nós [seu diferencial] para que [benefício para cliente]."
```

OBJEÇÕES VS CONCORRENTES:
- "Já uso [concorrente]" → Resposta: ___
- "Vocês são mais caros" → Resposta: ___
- "Nunca ouvi falar de vocês" → Resposta: ___

ENTREGÁVEIS:
- Mapa de concorrentes
- Matriz de diferenciação
- Pitch de 30 segundos
- Respostas para objeções'''
            },
            {
                'ordem': 3,
                'titulo': 'Definição de Metas e KPIs',
                'tempo_estimado': 60,
                'descricao': '''OBJETIVO: Estabelecer metas claras e mensuráveis para a prospecção.

METAS SMART:
- Specific (Específica)
- Measurable (Mensurável)
- Achievable (Alcançável)
- Relevant (Relevante)
- Time-bound (Com prazo)

EXEMPLO RUIM: "Quero mais clientes"
EXEMPLO BOM: "Agendar 20 reuniões qualificadas por mês até março/2026"

KPIs DE PROSPECÇÃO:

1. VOLUME (Atividade)
   - Emails enviados/dia
   - Conexões LinkedIn/dia
   - Ligações realizadas/dia
   - Prospects abordados/semana

2. QUALIDADE (Conversão)
   - Taxa de abertura de email (meta: >40%)
   - Taxa de resposta email (meta: >5%)
   - Taxa de conexão LinkedIn (meta: >30%)
   - Taxa de resposta LinkedIn (meta: >15%)
   - Taxa de conversão ligação (meta: >3%)

3. RESULTADO (Output)
   - Reuniões agendadas/semana
   - Reuniões realizadas (descontar no-show)
   - Oportunidades geradas
   - Pipeline criado (R$)

4. EFICIÊNCIA
   - Touchpoints até conversão (meta: <12)
   - Tempo médio até reunião (meta: <21 dias)
   - Custo por lead (CPL)
   - Custo por reunião

CALCULANDO METAS REVERSAS:
```
Meta: 10 clientes/mês
Taxa de fechamento: 25%
→ Preciso de 40 oportunidades

Taxa de qualificação: 50%
→ Preciso de 80 reuniões

Taxa de agendamento: 10%
→ Preciso abordar 800 prospects

Com 22 dias úteis:
→ 36 prospects/dia
```

ENTREGÁVEIS:
- Metas mensais definidas
- KPIs com valores-alvo
- Dashboard de acompanhamento
- Rotina de revisão semanal'''
            },
            {
                'ordem': 4,
                'titulo': 'Mapeamento da Jornada de Compra',
                'tempo_estimado': 90,
                'descricao': '''OBJETIVO: Entender como seu cliente compra para alinhar a abordagem.

JORNADA TÍPICA B2B:

1. APRENDIZADO (Topo do Funil)
   - Cliente não sabe que tem problema
   - Busca informações genéricas
   - Consome conteúdo educativo

2. RECONHECIMENTO DO PROBLEMA
   - Identifica que tem uma dor
   - Começa a pesquisar soluções
   - Compara alternativas

3. CONSIDERAÇÃO
   - Avalia fornecedores
   - Pede demonstrações
   - Envolve outros decisores

4. DECISÃO
   - Negocia proposta
   - Valida com stakeholders
   - Fecha contrato

PERGUNTAS POR ETAPA:

Aprendizado:
- Como o cliente descobre que tem o problema?
- Que conteúdo consome?
- Onde busca informação?

Reconhecimento:
- Quais gatilhos fazem ele agir?
- Que perguntas ele faz?
- Quem ele consulta?

Consideração:
- Que critérios usa para avaliar?
- Quem mais participa da decisão?
- Quais objeções surgem?

Decisão:
- Quanto tempo leva para decidir?
- Que aprovações precisa?
- O que trava a decisão?

MAPEAMENTO DE STAKEHOLDERS:
```
| Papel          | Cargo típico    | O que quer          |
|----------------|-----------------|---------------------|
| Decisor        | CEO, Diretor    | ROI, resultado      |
| Influenciador  | Gerente, Coord  | Facilidade, suporte |
| Usuário        | Analista        | Usabilidade         |
| Financeiro     | CFO, Compras    | Preço, condições    |
```

ENTREGÁVEIS:
- Jornada de compra mapeada
- Conteúdo por etapa definido
- Stakeholders identificados
- Objeções por etapa'''
            },

            # =====================================
            # FASE 2: SETUP DE FERRAMENTAS
            # =====================================
            {
                'ordem': 5,
                'titulo': 'Setup de Ferramentas de Prospecção',
                'tempo_estimado': 240,
                'descricao': '''OBJETIVO: Configurar as ferramentas necessárias para prospecção.

STACK MÍNIMO RECOMENDADO:

1. CRM (Gestão de Relacionamento)
   Opções:
   - HubSpot (gratuito até certo ponto)
   - Pipedrive (visual, fácil)
   - RD Station CRM (brasileiro)

   Configurar:
   - [ ] Funil de prospecção
   - [ ] Campos customizados (ICP data)
   - [ ] Automações básicas
   - [ ] Integração com email

2. FERRAMENTA DE EMAIL
   Opções:
   - Instantly (alto volume)
   - Lemlist (personalização)
   - Saleshandy (simples)

   Configurar:
   - [ ] Domínio dedicado para cold email
   - [ ] SPF, DKIM, DMARC
   - [ ] Aquecimento de domínio (2 semanas)
   - [ ] Templates de sequência

3. LINKEDIN SALES NAVIGATOR
   - [ ] Contratar licença
   - [ ] Configurar filtros salvos
   - [ ] Criar listas de leads
   - [ ] Instalar extensão de CRM

4. FERRAMENTA DE DADOS/ENRIQUECIMENTO
   Opções:
   - Apollo.io (completo)
   - Lusha (emails/telefones)
   - Snov.io (email finder)

   Configurar:
   - [ ] Conta criada
   - [ ] Créditos adquiridos
   - [ ] Integração com CRM

5. TELEFONIA (se usar ligações)
   Opções:
   - Aircall
   - JustCall
   - PhoneTrack (BR)

CONFIGURAÇÃO DE EMAIL FRIO:

Domínio novo:
- Comprar domínio similar (ex: suaempresa.co)
- Criar email (ex: nome@suaempresa.co)
- Configurar autenticações

Aquecimento (OBRIGATÓRIO):
- Usar ferramenta de warm-up
- 2-3 semanas antes de enviar
- Começar com 10/dia, aumentar gradualmente

INTEGRAÇÕES:
- CRM ↔ Ferramenta de email
- CRM ↔ LinkedIn
- Calendário para agendamentos

ENTREGÁVEIS:
- Ferramentas contratadas
- Integrações funcionando
- Email aquecido
- CRM configurado'''
            },
            {
                'ordem': 6,
                'titulo': 'Criação de Perfis e Presença Digital',
                'tempo_estimado': 180,
                'descricao': '''OBJETIVO: Otimizar perfis para gerar credibilidade.

LINKEDIN PESSOAL (do prospectador):

1. FOTO DE PERFIL
   - Profissional, sorrindo
   - Fundo limpo
   - Rosto visível (não logo)

2. BANNER
   - Proposta de valor clara
   - Visual profissional
   - Contato ou CTA

3. HEADLINE (Título)
   Ruim: "Vendedor na Empresa X"
   Bom: "Ajudo [ICP] a [resultado] | [Empresa]"

   Exemplo:
   "Ajudo e-commerces a aumentar vendas em 40% com automação | Growth na TechCorp"

4. SOBRE (About)
   Estrutura:
   - Gancho (problema que resolve)
   - Para quem (ICP)
   - Como ajuda (solução)
   - Prova (resultados/números)
   - CTA (como entrar em contato)

5. EXPERIÊNCIA
   - Resultados, não tarefas
   - Números sempre que possível
   - Keywords relevantes

6. RECOMENDAÇÕES
   - Pedir para clientes satisfeitos
   - Mínimo 3-5 recomendações

LINKEDIN DA EMPRESA:

- [ ] Página atualizada
- [ ] Descrição clara
- [ ] Posts regulares
- [ ] Cases/depoimentos

OUTROS CANAIS:

Instagram (se relevante):
- [ ] Bio profissional
- [ ] Destaques organizados
- [ ] Conteúdo de valor

Email Signature:
```
Nome Sobrenome
Cargo | Empresa
📞 (11) 99999-9999
📅 Agendar conversa: [link calendly]
```

ENTREGÁVEIS:
- LinkedIn pessoal otimizado
- LinkedIn empresa atualizado
- Assinatura de email padronizada
- Foto e banner profissionais'''
            },

            # =====================================
            # FASE 3: CONSTRUÇÃO DE LISTAS
            # =====================================
            {
                'ordem': 7,
                'titulo': 'Construção de Lista de Prospects',
                'tempo_estimado': 300,
                'descricao': '''OBJETIVO: Criar lista qualificada de prospects dentro do ICP.

FONTES DE DADOS:

1. LINKEDIN SALES NAVIGATOR
   Filtros poderosos:
   - Cargo (título exato ou similar)
   - Setor da empresa
   - Tamanho da empresa
   - Região
   - Mudou de emprego recentemente
   - Postou conteúdo recentemente

   Como usar:
   - Criar busca com filtros do ICP
   - Salvar como lista
   - Exportar com ferramenta (Apollo, Lusha)

2. APOLLO.IO / LUSHA
   - Buscar por filtros similares
   - Enriquecer com email/telefone
   - Verificar dados antes de usar

3. GOOGLE + LINKEDIN
   Busca avançada:
   ```
   site:linkedin.com/in "[cargo]" "[empresa]"
   site:linkedin.com "[cargo]" "[setor]" "[cidade]"
   ```

4. LISTAS DE EMPRESAS
   - Ranking de maiores empresas do setor
   - Listas de startups (Crunchbase, Distrito)
   - Associações de classe
   - Eventos do setor

5. GATILHOS (Intent Data)
   - Vagas abertas (empresa crescendo)
   - Notícias (investimento, expansão)
   - Mudança de cargo no LinkedIn
   - Tecnologias usadas (BuiltWith)

QUALIDADE > QUANTIDADE:
- 100 prospects bem qualificados
- > 1000 prospects genéricos

ESTRUTURA DA LISTA:
```
| Nome | Cargo | Empresa | Email | Telefone | LinkedIn | Gatilho |
```

VALIDAÇÃO DE DADOS:
- Verificar emails antes de enviar
- Usar ferramentas de validação
- Taxa de bounce < 3%

ORGANIZAÇÃO:
- Segmentar por ICP tier (A, B, C)
- Priorizar por gatilho
- Separar por cadência

META: 200-500 prospects qualificados para começar

ENTREGÁVEIS:
- Lista de prospects no CRM
- Dados enriquecidos (email, telefone)
- Segmentação por prioridade
- Gatilhos identificados'''
            },
            {
                'ordem': 8,
                'titulo': 'Pesquisa e Personalização por Conta',
                'tempo_estimado': 240,
                'descricao': '''OBJETIVO: Pesquisar cada prospect para personalização relevante.

POR QUE PERSONALIZAR:
- Emails personalizados: 15-30% resposta
- Emails genéricos: 1-3% resposta
- Diferença de 10x no resultado!

O QUE PESQUISAR (por prospect):

1. SOBRE A PESSOA
   - Posts recentes no LinkedIn
   - Artigos publicados
   - Mudança de emprego
   - Promoção recente
   - Interesses/hobbies (se visível)
   - Conexões em comum

2. SOBRE A EMPRESA
   - Notícias recentes
   - Vagas abertas (indica prioridades)
   - Tecnologias usadas
   - Concorrentes
   - Tamanho e crescimento
   - Investimentos recebidos

3. GATILHOS ESPECÍFICOS
   - Evento que participou
   - Conteúdo que compartilhou
   - Comentário que fez
   - Mudança organizacional

NÍVEIS DE PERSONALIZAÇÃO:

Nível 1 (Mínimo):
- Nome e empresa corretos
- Cargo mencionado

Nível 2 (Bom):
- Gatilho específico (notícia, post)
- Dor relevante para o cargo

Nível 3 (Excelente):
- Referência a conteúdo que postou
- Insight específico sobre a empresa
- Conexão em comum mencionada

TEMPLATE DE PESQUISA:
```
Prospect: _______________
Empresa: _______________

Gatilho encontrado:
_______________

Dor provável:
_______________

Icebreaker personalizado:
_______________

Conexão em comum:
_______________
```

QUANTO TEMPO GASTAR:
- Tier A (alta prioridade): 10-15 min
- Tier B (média): 5-10 min
- Tier C (baixa): 2-5 min

ENTREGÁVEIS:
- Pesquisa documentada por prospect
- Icebreakers personalizados prontos
- Gatilhos mapeados
- Priorização atualizada'''
            },

            # =====================================
            # FASE 4: CRIAÇÃO DE CONTEÚDO E SCRIPTS
            # =====================================
            {
                'ordem': 9,
                'titulo': 'Criação de Sequência de Emails',
                'tempo_estimado': 240,
                'descricao': '''OBJETIVO: Criar sequência de emails que converte.

ESTRUTURA DA SEQUÊNCIA (5-7 emails):

EMAIL 1 - GATILHO + VALOR (Dia 1)
```
Assunto: [Gatilho específico] (max 40 chars)

[Nome],

Vi que [gatilho - empresa contratando, expandiu, notícia].

[1 frase conectando gatilho com problema comum]

Ajudei [cliente similar] a [resultado com número].

Vale 15 min para ver se faz sentido?

[Assinatura curta]
```

EMAIL 2 - CASE/PROVA SOCIAL (Dia 4)
```
Assunto: Re: [assunto anterior]

[Nome],

Caso não tenha visto meu email anterior...

[Cliente do mesmo setor] tinha o mesmo desafio
com [problema]. Em [X meses], conseguiram [resultado].

Posso mostrar como em 15 min?

[Assinatura]
```

EMAIL 3 - CONTEÚDO DE VALOR (Dia 8)
```
Assunto: [Tema relevante] para [empresa]

[Nome],

Montei um [guia/checklist/artigo] sobre [tema]
que acho que você vai curtir:

[Link]

Sem compromisso - só achei relevante
para quem está lidando com [desafio].

[Assinatura]
```

EMAIL 4 - DIRETO AO PONTO (Dia 12)
```
Assunto: Pergunta rápida

[Nome],

Vou direto: [pergunta sobre dor/desafio]?

Se sim, tenho uma ideia que pode ajudar.
Se não, sem problemas - me avisa que paro por aqui.

[Assinatura]
```

EMAIL 5 - BREAK-UP (Dia 18)
```
Assunto: Fechando por aqui

[Nome],

Tentei algumas vezes, sem sucesso.

Vou assumir que [problema] não é prioridade agora.

Se mudar, é só responder este email.

Sucesso!

[Assinatura]
```

REGRAS DE OURO:
- Emails curtos (< 100 palavras)
- Um CTA por email
- Assuntos curtos (< 40 chars)
- Não usar imagens/HTML pesado
- Espaçamento: 3-4 dias entre emails

VARIAÇÕES PARA TESTE A/B:
- Testar 2-3 assuntos diferentes
- Testar abordagem direta vs curiosidade
- Testar com/sem case

ENTREGÁVEIS:
- Sequência de 5-7 emails
- Variações para teste A/B
- Emails configurados na ferramenta
- Tracking configurado'''
            },
            {
                'ordem': 10,
                'titulo': 'Criação de Mensagens LinkedIn',
                'tempo_estimado': 180,
                'descricao': '''OBJETIVO: Criar templates de mensagens para LinkedIn.

NOTA DE CONEXÃO (max 300 caracteres):

Versão 1 - Baseada em Conteúdo:
```
[Nome], curti seu post sobre [tema].
Trabalho com [área relacionada] e seria
ótimo trocar ideias. Vamos conectar?
```

Versão 2 - Baseada em Gatilho:
```
[Nome], parabéns pela [promoção/novo cargo]!
Ajudo [cargos como o dele] com [resultado].
Bora conectar?
```

Versão 3 - Conexão em Comum:
```
[Nome], vi que você conhece [conexão].
Também atuo com [área] e seria legal
trocar experiências.
```

PRIMEIRA MENSAGEM (após conexão):

Versão 1 - Pergunta:
```
[Nome], obrigado por conectar!

Pergunta rápida: como vocês estão
lidando com [problema comum] na [empresa]?

Tenho visto muitas empresas de [setor]
enfrentando isso.
```

Versão 2 - Oferta de valor:
```
[Nome], vi que a [empresa] está [gatilho].

Tenho um [material/guia] sobre isso que
acho que você ia curtir. Posso enviar?
```

Versão 3 - Case:
```
[Nome], trabalho com empresas de [setor]
e recentemente ajudei [empresa similar]
a [resultado].

Faria sentido uma conversa de 15 min
para ver se posso ajudar a [empresa] também?
```

FOLLOW-UP LINKEDIN:

Após 5-7 dias sem resposta:
```
[Nome], passando aqui novamente.

Sei que a agenda é corrida. Se preferir,
posso mandar um email com mais detalhes.

Qual seu melhor email?
```

REGRAS DO LINKEDIN:
- Mensagens curtas (< 400 caracteres = +22% resposta)
- Não fazer pitch na conexão
- Esperar aceitar antes de enviar mensagem
- Máximo 100 conexões/semana (evitar bloqueio)
- Personalizar pelo menos a primeira linha

ENTREGÁVEIS:
- 3 versões de nota de conexão
- 3 versões de primeira mensagem
- 2 versões de follow-up
- Sequência documentada'''
            },
            {
                'ordem': 11,
                'titulo': 'Criação de Script de Ligação',
                'tempo_estimado': 180,
                'descricao': '''OBJETIVO: Criar script de cold call eficiente.

ESTRUTURA DA LIGAÇÃO:

1. ABERTURA (10 segundos)
```
"Oi [Nome], aqui é [seu nome] da [empresa].
Peguei você em um momento ruim?"
```

Por que funciona:
- Pergunta desarma a resistência
- Dá controle ao prospect
- Mostra respeito pelo tempo

2. SE DISSE QUE PODE FALAR:
```
"Ótimo! Vou ser breve.

A gente ajuda [tipo de empresa] a
[resultado principal].

Recentemente, [cliente similar] conseguiu
[resultado específico].

Faria sentido uma conversa de 15 min
pra eu entender se podemos ajudar
a [empresa] também?"
```

3. SE PEDIU PARA SER RÁPIDO:
```
"Claro! Em uma frase: ajudamos [ICP]
a [resultado]. A [cliente] conseguiu
[número]. Vale 15 min pra explorar?"
```

TRATAMENTO DE OBJEÇÕES:

"Não tenho tempo":
```
"Entendo totalmente. Por isso sugiro só
15 min. Que tal [dia] às [hora]?"
```

"Manda por email":
```
"Claro! Para eu mandar algo relevante,
me conta: qual o maior desafio de vocês
hoje com [área]?"
```

"Já temos fornecedor":
```
"Faz sentido! A maioria dos nossos
clientes também tinha. A conversa
seria pra mostrar uma abordagem
diferente. Sem compromisso, vale conhecer?"
```

"Não tenho interesse":
```
"Entendo. Posso perguntar: é porque
[problema] não é prioridade agora
ou vocês já resolveram isso?"
```

"Quanto custa?":
```
"Depende muito do cenário de vocês.
Temos clientes pagando de X a Y.
Para te dar um número real, preciso
entender melhor a operação. Podemos
agendar 15 min?"
```

DEIXANDO VOICEMAIL:
```
"Oi [Nome], aqui é [seu nome] da [empresa].

Estou ligando porque ajudamos [empresas
como a dele] a [resultado].

Vou mandar um email com mais detalhes.
Meu número é [número].

Obrigado!"
```

(Max 30 segundos)

DICAS:
- Sorria ao falar (muda o tom)
- Fale devagar
- Pause após perguntas
- Anote tudo
- Ligue de pé (mais energia)

ENTREGÁVEIS:
- Script de abertura
- Pitch de 30 segundos
- Respostas para 5+ objeções
- Script de voicemail'''
            },

            # =====================================
            # FASE 5: EXECUÇÃO DA CADÊNCIA
            # =====================================
            {
                'ordem': 12,
                'titulo': 'Setup da Cadência Multicanal',
                'tempo_estimado': 120,
                'descricao': '''OBJETIVO: Configurar a cadência completa de touchpoints.

CADÊNCIA RECOMENDADA (21 dias, 12 touchpoints):

```
DIA 1:   LinkedIn - Visualizar perfil
DIA 2:   LinkedIn - Curtir posts + Conexão com nota
DIA 3:   Email 1 - Gatilho + Valor
DIA 5:   LinkedIn - Mensagem (se conectou)
DIA 7:   Email 2 - Case/Prova social
DIA 8:   Ligação 1 - Tentativa
DIA 10:  Email 3 - Conteúdo útil
DIA 12:  Ligação 2 - Tentativa
DIA 14:  LinkedIn - Engajar com conteúdo
DIA 16:  Email 4 - Direto ao ponto
DIA 18:  Ligação 3 - Última tentativa
DIA 21:  Email 5 - Break-up
```

CONFIGURAR NA FERRAMENTA:

1. SEQUÊNCIA DE EMAIL
   - Criar sequência com intervalos
   - Configurar horários de envio
   - Ativar tracking (abertura, clique)
   - Pausar se responder

2. TAREFAS MANUAIS
   - LinkedIn (não automatizar demais)
   - Ligações
   - Follow-ups especiais

3. REGRAS DE SAÍDA
   - Resposta positiva → Parar cadência
   - Resposta negativa → Parar cadência
   - Bounce → Remover da lista
   - Unsubscribe → Nunca mais contatar

HORÁRIOS IDEAIS:

Email:
- Terça a quinta
- 8-10h ou 14-16h
- Evitar segunda e sexta

LinkedIn:
- Terça a quinta
- 7-9h ou 17-19h

Ligação:
- 8-9h ou 16-17h
- Evitar almoço (11-14h)

VOLUME DIÁRIO RECOMENDADO:
- Emails: 30-50/dia (novo domínio)
- Conexões LinkedIn: 20-25/dia
- Ligações: 40-50/dia

ENTREGÁVEIS:
- Cadência configurada na ferramenta
- Automações ativas
- Tarefas manuais agendadas
- Regras de saída definidas'''
            },
            {
                'ordem': 13,
                'titulo': 'Início da Prospecção - Semana 1',
                'tempo_estimado': 480,
                'descricao': '''OBJETIVO: Executar primeira semana de prospecção ativa.

ANTES DE COMEÇAR:
- [ ] Ferramentas testadas
- [ ] Emails aquecidos (se novo domínio)
- [ ] Lista de prospects carregada
- [ ] Sequências configuradas
- [ ] CRM organizado

DIA A DIA:

SEGUNDA-FEIRA:
- Revisar lista de prospects da semana
- Verificar respostas do fim de semana
- Iniciar 20-30 novas cadências
- Fazer pesquisa para personalização

TERÇA-FEIRA:
- Enviar conexões LinkedIn (20-25)
- Fazer ligações de follow-up
- Enviar primeiros emails
- Documentar objeções novas

QUARTA-FEIRA:
- Continuar cadências
- Ligar para quem abriu email
- Responder mensagens LinkedIn
- Ajustar scripts se necessário

QUINTA-FEIRA:
- Maior volume de atividade
- Ligações prioritárias
- Follow-ups de email
- Conexões LinkedIn

SEXTA-FEIRA:
- Revisar métricas da semana
- Limpar lista (bounces, respostas negativas)
- Preparar próxima semana
- Documentar aprendizados

TRACKING DIÁRIO:
```
| Métrica              | Meta  | Real |
|----------------------|-------|------|
| Emails enviados      | 30    |      |
| Conexões LinkedIn    | 20    |      |
| Ligações realizadas  | 40    |      |
| Respostas recebidas  |       |      |
| Reuniões agendadas   |       |      |
```

SINAIS DE AJUSTE:
- Taxa de abertura < 30% → Mudar assuntos
- Taxa de resposta < 3% → Mudar copy
- Taxa de conexão < 20% → Mudar nota
- Muitas objeções iguais → Ajustar pitch

ENTREGÁVEIS:
- 100-150 prospects em cadência
- Métricas documentadas
- Ajustes identificados
- Reuniões na agenda'''
            },
            {
                'ordem': 14,
                'titulo': 'Prospecção Contínua - Semanas 2-4',
                'tempo_estimado': 960,
                'descricao': '''OBJETIVO: Manter ritmo e otimizar baseado em dados.

ROTINA SEMANAL:

INÍCIO DA SEMANA:
1. Revisar métricas da semana anterior
2. Adicionar novos prospects à cadência
3. Priorizar follow-ups quentes
4. Ajustar scripts se necessário

MEIO DA SEMANA:
1. Máximo volume de atividades
2. Ligar para quem engajou (abriu email, viu perfil)
3. Responder todas as mensagens em < 24h
4. Documentar objeções e respostas

FIM DA SEMANA:
1. Limpar lista (remover bounces, negativos)
2. Calcular métricas
3. Identificar o que funcionou
4. Preparar próxima semana

ANÁLISE DE MÉTRICAS:

Semana 2 - Primeiros dados:
- Quais assuntos têm mais abertura?
- Quais mensagens têm mais resposta?
- Em que horário funciona melhor?

Semana 3 - Ajustes:
- Dobrar o que funciona
- Parar o que não funciona
- Testar novas variações

Semana 4 - Otimização:
- Sequência otimizada
- Melhores práticas documentadas
- Processo repetível

GESTÃO DO PIPELINE:

Prospects em cadência:
- Manter 150-300 ativos
- Adicionar novos conforme saem
- Não deixar "morrer"

Respostas positivas:
- Responder em < 2 horas
- Agendar reunião imediatamente
- Enviar confirmação + agenda

Respostas negativas:
- Agradecer educadamente
- Perguntar se pode contatar no futuro
- Marcar no CRM

Sem resposta após cadência:
- Mover para "nurturing"
- Recontatar em 3-6 meses
- Adicionar em newsletter

ENTREGÁVEIS:
- Pipeline ativo de 150-300 prospects
- 8-15 reuniões agendadas
- Métricas semanais
- Processo documentado'''
            },

            # =====================================
            # FASE 6: QUALIFICAÇÃO E REUNIÕES
            # =====================================
            {
                'ordem': 15,
                'titulo': 'Processo de Qualificação (BANT/SPIN)',
                'tempo_estimado': 120,
                'descricao': '''OBJETIVO: Qualificar leads antes/durante a reunião.

POR QUE QUALIFICAR:
- Não perder tempo com quem não vai comprar
- Focar energia nos mais promissores
- Melhorar taxa de fechamento

FRAMEWORK BANT:

B - BUDGET (Orçamento)
Perguntas:
- "Vocês têm orçamento reservado para isso?"
- "Quanto investem hoje em [área]?"
- "Qual range de investimento faz sentido?"

A - AUTHORITY (Autoridade)
Perguntas:
- "Quem mais participa dessa decisão?"
- "Como funciona o processo de compra aí?"
- "Você consegue aprovar sozinho?"

N - NEED (Necessidade)
Perguntas:
- "Qual o maior desafio hoje com [área]?"
- "O que acontece se não resolver isso?"
- "Há quanto tempo enfrentam esse problema?"

T - TIMELINE (Prazo)
Perguntas:
- "Para quando precisam resolver isso?"
- "Existe algum prazo ou deadline?"
- "O que precisa acontecer para começar?"

FRAMEWORK SPIN:

S - SITUATION (Situação)
"Como funciona [processo] hoje?"
"Quantas pessoas envolvidas?"
"Que ferramenta usam?"

P - PROBLEM (Problema)
"O que não funciona bem?"
"Onde perdem mais tempo?"
"O que mais frustra a equipe?"

I - IMPLICATION (Implicação)
"Quanto isso custa por mês?"
"Como afeta [outra área]?"
"O que acontece se continuar assim?"

N - NEED-PAYOFF (Necessidade/Benefício)
"Se resolvesse isso, o que mudaria?"
"Quanto valeria resolver?"
"O que seria possível fazer?"

SCORECARD DE QUALIFICAÇÃO:
```
| Critério        | Peso | Nota (1-5) | Score |
|-----------------|------|------------|-------|
| Fit com ICP     | 3    |            |       |
| Dor clara       | 3    |            |       |
| Budget existe   | 2    |            |       |
| Decisor         | 2    |            |       |
| Timeline < 90d  | 1    |            |       |
| TOTAL           |      |            | /55   |
```

Score > 40 = Qualificado
Score 25-40 = Nurturing
Score < 25 = Desqualificar

ENTREGÁVEIS:
- Framework de qualificação escolhido
- Perguntas prontas
- Scorecard configurado no CRM
- Critérios de go/no-go definidos'''
            },
            {
                'ordem': 16,
                'titulo': 'Preparação para Reuniões',
                'tempo_estimado': 60,
                'descricao': '''OBJETIVO: Preparar cada reunião para maximizar conversão.

ANTES DA REUNIÃO (30 min prep):

1. PESQUISA ADICIONAL
   - LinkedIn do prospect (atualizado)
   - Site da empresa
   - Notícias recentes
   - Glassdoor (cultura)
   - Reclame Aqui (se B2C)

2. REVISAR HISTÓRICO
   - Como chegou até você
   - Emails trocados
   - O que demonstrou interesse
   - Dores mencionadas

3. PREPARAR AGENDA
   ```
   Agenda sugerida (30 min):

   1. Introduções (2 min)
   2. Contexto/situação atual (8 min)
   3. Dores e desafios (10 min)
   4. Nossa solução (5 min)
   5. Próximos passos (5 min)
   ```

4. PREPARAR PERGUNTAS
   - 3-5 perguntas de descoberta
   - Perguntas de qualificação
   - Pergunta de fechamento

5. PREPARAR DEMONSTRAÇÃO
   - Caso relevante pronto
   - Demo personalizada (se aplicável)
   - Materiais de apoio

CHECKLIST PRÉ-REUNIÃO:
- [ ] Link de videoconferência testado
- [ ] Câmera e microfone funcionando
- [ ] Ambiente silencioso
- [ ] Materiais abertos
- [ ] CRM aberto para anotações
- [ ] Calendário aberto (para agendar próximo passo)

CONFIRMAÇÃO:
Enviar no dia anterior:
```
Oi [Nome]!

Confirmando nossa conversa amanhã às [hora].

Link: [link]

Agenda:
- Entender seu cenário atual
- Mostrar como podemos ajudar
- Definir próximos passos (se fizer sentido)

Até amanhã!
```

NO-SHOW (se não aparecer):
Esperar 5 min, depois:
```
Oi [Nome], estou na call.
Aconteceu algum imprevisto?
Podemos reagendar se preferir.
```

ENTREGÁVEIS:
- Template de preparação
- Agenda padrão
- Email de confirmação
- Protocolo de no-show'''
            },
            {
                'ordem': 17,
                'titulo': 'Condução de Reuniões de Discovery',
                'tempo_estimado': 120,
                'descricao': '''OBJETIVO: Conduzir reuniões que convertem em oportunidades.

ESTRUTURA DA REUNIÃO (30-45 min):

1. ABERTURA (2-3 min)
```
"[Nome], obrigado pelo tempo!

Pensei em estruturar assim nossa conversa:
- Primeiro, entender melhor seu cenário
- Depois, mostrar como temos ajudado empresas similares
- E aí definimos se faz sentido continuar

Funciona pra você?"
```

2. DESCOBERTA (15-20 min)
```
Situação atual:
- "Me conta um pouco sobre como funciona [área] hoje?"
- "Quantas pessoas na equipe?"
- "Que ferramentas usam?"

Problemas:
- "O que não funciona tão bem?"
- "Onde vocês perdem mais tempo?"
- "Se pudesse mudar uma coisa, o que seria?"

Impacto:
- "Quanto isso custa por mês, você tem ideia?"
- "Como isso afeta [outras áreas]?"
- "O que acontece se continuar assim?"

Solução ideal:
- "Como seria o cenário ideal pra vocês?"
- "O que precisa acontecer pra resolver?"
```

3. APRESENTAÇÃO (10 min)
```
"Baseado no que você me contou...

[Resumir as dores principais]

A gente ajuda com isso através de [solução resumida].

Por exemplo, [caso similar]:
- Situação parecida com a de vocês
- Implementamos [solução]
- Resultado: [número específico]

Posso mostrar rapidamente como funciona?"
```

4. FECHAMENTO (5 min)
```
"[Nome], baseado na nossa conversa...

Faz sentido explorar isso mais a fundo?

[Se sim]
Próximo passo seria [demo detalhada/proposta/reunião com time].
Você consegue [data]?

[Se talvez]
Entendo. O que você precisaria ver/saber
pra se sentir confortável em avançar?

[Se não]
Sem problemas. Posso perguntar o que
faltou ou não se encaixou?
```

DICAS:
- Fale 30%, ouça 70%
- Anote TUDO
- Confirme entendimento ("Se entendi bem...")
- Não tenha medo do silêncio
- Sempre defina próximo passo

APÓS A REUNIÃO:
1. Enviar resumo por email (< 1 hora)
2. Atualizar CRM
3. Agendar próximo passo
4. Enviar materiais prometidos

ENTREGÁVEIS:
- Script de reunião
- Perguntas de descoberta
- Template de follow-up
- Checklist pós-reunião'''
            },

            # =====================================
            # FASE 7: FOLLOW-UP E NURTURING
            # =====================================
            {
                'ordem': 18,
                'titulo': 'Processo de Follow-up Pós-Reunião',
                'tempo_estimado': 90,
                'descricao': '''OBJETIVO: Manter momentum após reuniões.

EMAIL DE FOLLOW-UP (enviar em < 1 hora):

```
Assunto: Resumo da nossa conversa + próximos passos

[Nome],

Obrigado pela conversa!

Resumo do que discutimos:

SITUAÇÃO ATUAL:
- [Ponto 1 que ele mencionou]
- [Ponto 2]

PRINCIPAIS DESAFIOS:
- [Dor 1]
- [Dor 2]

COMO PODEMOS AJUDAR:
- [Solução 1 conectada à dor]
- [Solução 2]

PRÓXIMOS PASSOS:
- [O que vocês combinaram]
- Data: [data acordada]

Materiais:
- [Link para case mencionado]
- [Link para material relevante]

Alguma dúvida enquanto isso?

[Assinatura]
```

CADÊNCIA DE FOLLOW-UP PÓS-REUNIÃO:

Se próximo passo definido:
```
Dia 0: Email resumo (< 1 hora)
Dia -1: Confirmação do próximo passo
Dia +1: Verificar se tem dúvidas
```

Se ficou de "pensar":
```
Dia 0: Email resumo
Dia 3: "Alguma dúvida?"
Dia 7: Novo insight/case
Dia 14: "Faz sentido retomarmos?"
Dia 21: Break-up educado
```

Se não respondeu:
```
Dia 3: Bump simples
Dia 7: Novo ângulo/valor
Dia 14: Último follow-up
```

TEMPLATES:

Follow-up "Pensando":
```
[Nome], passando aqui.

Enquanto vocês avaliam, achei que
esse caso da [empresa similar] seria
relevante: [link]

Ficou alguma dúvida da nossa conversa?
```

Follow-up "Sumiu":
```
[Nome], você sumiu! Tudo bem?

Fico imaginando se:
a) Não é prioridade agora
b) Está avaliando outras opções
c) Precisa de mais informações

Me ajuda a entender?
```

REGRAS:
- Sempre agregar valor, não só cobrar
- Máximo 5-7 follow-ups
- Espaçar adequadamente
- Respeitar se pedir para parar

ENTREGÁVEIS:
- Template de email resumo
- Cadência de follow-up
- Templates por situação
- Automação configurada'''
            },
            {
                'ordem': 19,
                'titulo': 'Nurturing de Leads Não-Prontos',
                'tempo_estimado': 120,
                'descricao': '''OBJETIVO: Manter relacionamento com leads que não estão prontos agora.

QUANDO FAZER NURTURING:
- "Gostei, mas não é o momento"
- "Preciso de budget ano que vem"
- "Estamos em outro projeto agora"
- Não respondeu mas é ICP bom

ESTRATÉGIAS DE NURTURING:

1. NEWSLETTER/EMAIL MARKETING
   - Adicionar em lista segmentada
   - Conteúdo relevante mensal
   - Não fazer pitch direto
   - Manter top of mind

2. LINKEDIN
   - Manter conectado
   - Curtir/comentar posts
   - Compartilhar conteúdo relevante
   - Engajar naturalmente

3. RECONTATO PROGRAMADO
   - Definir data de recontato no CRM
   - Gatilhos para reativar:
     * Mudou de cargo
     * Empresa recebeu investimento
     * Final do trimestre/ano
     * Novo produto lançado

CADÊNCIA DE NURTURING:

Mês 1:
- Semana 2: Conteúdo educativo

Mês 2:
- Semana 1: Case de sucesso novo

Mês 3:
- Semana 2: Convite para webinar/evento
- Semana 4: Check-in pessoal

Mês 4-6:
- 1 touchpoint por mês
- Alternar conteúdo e check-ins

TEMPLATES:

Check-in trimestral:
```
[Nome], tudo bem?

Passando aqui pra ver como estão
as coisas na [empresa].

Quando conversamos em [mês], vocês
estavam lidando com [desafio].
Conseguiram resolver?

Qualquer novidade, fico à disposição.
```

Reativação por gatilho:
```
[Nome], vi que a [empresa] [gatilho].

Parabéns! Isso geralmente traz
novos desafios com [área relacionada].

Faz sentido uma conversa rápida
pra ver se podemos ajudar nessa fase?
```

MÉTRICAS DE NURTURING:
- Taxa de abertura > 30%
- Taxa de reativação > 5%
- Tempo médio para conversão

ENTREGÁVEIS:
- Processo de nurturing documentado
- Cadência configurada
- Segmentos no CRM
- Templates de reativação'''
            },

            # =====================================
            # FASE 8: OTIMIZAÇÃO E ESCALA
            # =====================================
            {
                'ordem': 20,
                'titulo': 'Análise de Métricas e Otimização',
                'tempo_estimado': 180,
                'descricao': '''OBJETIVO: Analisar resultados e otimizar continuamente.

MÉTRICAS PARA ANALISAR:

1. TOPO DO FUNIL (Atividade)
   ```
   | Métrica              | Meta    | Real | Status |
   |----------------------|---------|------|--------|
   | Emails enviados/dia  | 30-50   |      |        |
   | Conexões LinkedIn    | 20-25   |      |        |
   | Ligações/dia         | 40-50   |      |        |
   ```

2. MEIO DO FUNIL (Conversão)
   ```
   | Métrica                 | Meta   | Real | Status |
   |-------------------------|--------|------|--------|
   | Taxa abertura email     | > 40%  |      |        |
   | Taxa resposta email     | > 5%   |      |        |
   | Taxa conexão LinkedIn   | > 30%  |      |        |
   | Taxa resposta LinkedIn  | > 15%  |      |        |
   | Taxa conversão ligação  | > 3%   |      |        |
   ```

3. FUNDO DO FUNIL (Resultado)
   ```
   | Métrica              | Meta   | Real | Status |
   |----------------------|--------|------|--------|
   | Reuniões agendadas   | 15-20  |      |        |
   | Taxa no-show         | < 20%  |      |        |
   | Reuniões realizadas  |        |      |        |
   | Oportunidades criadas|        |      |        |
   ```

ANÁLISE POR CANAL:

Qual canal gera mais reuniões?
Qual tem melhor custo-benefício?
Onde focar mais?

TESTES A/B:

O que testar:
- Assuntos de email (2-3 variações)
- Horários de envio
- Abordagens (dor vs benefício)
- CTAs diferentes
- Com/sem case

Como testar:
- Uma variável por vez
- Mínimo 50 envios por variação
- Esperar resultado estatístico
- Implementar vencedor

OTIMIZAÇÕES COMUNS:

Taxa abertura baixa (<30%):
→ Melhorar assuntos
→ Testar horários
→ Verificar entregabilidade

Taxa resposta baixa (<3%):
→ Mais personalização
→ Mensagens mais curtas
→ CTA mais claro
→ Proposta de valor mais forte

Taxa conexão baixa (<20%):
→ Melhorar headline do perfil
→ Personalizar nota de conexão
→ Foto profissional

Muitos no-shows (>25%):
→ Confirmar no dia anterior
→ Lembrete 1h antes
→ Reduzir tempo até reunião

DOCUMENTAR APRENDIZADOS:

O que funciona:
- Assunto X tem 50% abertura
- Ligar às 9h converte melhor
- Case da empresa Y ressoa

O que não funciona:
- Abordagem Z gera rejeição
- Sexta-feira tem baixa resposta
- Mensagens > 500 chars não funcionam

ENTREGÁVEIS:
- Dashboard de métricas
- Testes A/B documentados
- Playbook de otimizações
- Reunião semanal de análise'''
            },
            {
                'ordem': 21,
                'titulo': 'Documentação e Playbook',
                'tempo_estimado': 180,
                'descricao': '''OBJETIVO: Documentar processo para replicar e escalar.

PLAYBOOK DE PROSPECÇÃO:

1. VISÃO GERAL
   - ICP definido
   - Proposta de valor
   - Diferenciais competitivos

2. FERRAMENTAS
   - Stack utilizado
   - Logins e acessos
   - Integrações

3. LISTAS E FONTES
   - Como construir listas
   - Fontes de dados
   - Critérios de qualificação

4. CADÊNCIAS
   - Sequência de emails
   - Sequência LinkedIn
   - Roteiro de ligações
   - Timing e frequência

5. TEMPLATES
   - Todos os templates de email
   - Mensagens LinkedIn
   - Scripts de ligação
   - Respostas para objeções

6. MÉTRICAS
   - KPIs e metas
   - Como medir
   - Frequência de análise

7. PROCESSOS
   - Rotina diária
   - Rotina semanal
   - Handoff para vendas

FORMATO SUGERIDO:

```
PLAYBOOK DE PROSPECÇÃO ATIVA
[Nome da Empresa]
Versão: 1.0
Data: [data]

SUMÁRIO:
1. ICP e Personas
2. Ferramentas e Acessos
3. Construção de Listas
4. Cadência Multicanal
5. Templates e Scripts
6. Qualificação
7. Métricas e Análise
8. FAQ e Troubleshooting
```

CHECKLIST DO PLAYBOOK:

Estratégia:
- [ ] ICP documentado
- [ ] Proposta de valor clara
- [ ] Diferencial mapeado

Execução:
- [ ] Cadências detalhadas
- [ ] Templates prontos
- [ ] Scripts de ligação
- [ ] Objeções e respostas

Processo:
- [ ] Rotina diária definida
- [ ] Métricas estabelecidas
- [ ] Ferramentas documentadas

Treinamento:
- [ ] Onboarding de novos SDRs
- [ ] Gravações de calls boas
- [ ] FAQ atualizado

ENTREGÁVEIS:
- Playbook completo (PDF/Notion)
- Templates exportados
- Acessos documentados
- Processo de atualização'''
            },
            {
                'ordem': 22,
                'titulo': 'Escala e Automação Avançada',
                'tempo_estimado': 240,
                'descricao': '''OBJETIVO: Escalar a operação de prospecção.

QUANDO ESCALAR:
- Processo validado (taxa de conversão estável)
- Métricas dentro da meta
- Demanda > capacidade
- ROI positivo comprovado

FORMAS DE ESCALAR:

1. AUMENTAR VOLUME (mesmo processo)
   - Mais prospects por dia
   - Mais sequências simultâneas
   - Cuidado com qualidade

2. CONTRATAR SDRs
   - Perfil ideal de SDR
   - Processo de onboarding
   - Treinamento com playbook
   - Ramp-up de 2-3 meses

3. AUTOMAÇÃO AVANÇADA

   Email:
   - Múltiplos domínios
   - Rotação de remetentes
   - Personalização com IA

   LinkedIn:
   - Ferramentas de automação (cuidado!)
   - Limites seguros
   - Variação de mensagens

   Dados:
   - Enriquecimento automático
   - Intent data
   - Triggers automáticos

4. TERCEIRIZAÇÃO
   - Agências de prospecção
   - SDRs terceirizados
   - Prós: escala rápida
   - Contras: menos controle

ESTRUTURA DE TIME:

1 SDR:
- 150-300 prospects em cadência
- 15-25 reuniões/mês
- 1 segmento/vertical

2-3 SDRs:
- Segmentar por vertical
- Ou por região
- Compartilhar aprendizados

4+ SDRs:
- Líder/coordenador
- Especialização
- Processo de coaching

AUTOMAÇÃO COM IA:

O que automatizar:
- Pesquisa de prospects
- Geração de icebreakers
- Personalização de emails
- Classificação de respostas
- Agendamento de reuniões

O que NÃO automatizar:
- Relacionamento de alto valor
- Negociações complexas
- Contas estratégicas

FERRAMENTAS DE ESCALA:
- Clay (enriquecimento + workflows)
- ChatGPT/Claude (personalização)
- Zapier (automações)
- AI SDRs (Nooks, AiSDR, etc)

MÉTRICAS DE ESCALA:
- Custo por reunião
- Tempo de ramp-up
- Qualidade vs volume
- CAC por canal

ENTREGÁVEIS:
- Plano de escala
- Processo de contratação
- Automações implementadas
- Métricas de escala'''
            },

            # =====================================
            # FASE 9: MELHORIA CONTÍNUA
            # =====================================
            {
                'ordem': 23,
                'titulo': 'Revisão Mensal e Ajustes',
                'tempo_estimado': 120,
                'descricao': '''OBJETIVO: Revisar resultados mensais e fazer ajustes estratégicos.

REUNIÃO MENSAL DE REVISÃO:

AGENDA (1-2 horas):

1. RESULTADOS DO MÊS (15 min)
   - Reuniões agendadas vs meta
   - Taxa de conversão por canal
   - Pipeline gerado
   - Qualidade dos leads

2. ANÁLISE DE MÉTRICAS (20 min)
   - O que funcionou
   - O que não funcionou
   - Tendências identificadas
   - Anomalias

3. FEEDBACK QUALITATIVO (15 min)
   - Principais objeções ouvidas
   - Mudanças no mercado
   - Feedback de vendas sobre qualidade
   - Novos concorrentes/ofertas

4. AÇÕES DO MÊS ANTERIOR (10 min)
   - O que foi implementado
   - Resultados dos testes
   - O que ficou pendente

5. PLANO PARA PRÓXIMO MÊS (30 min)
   - Metas ajustadas
   - Testes a realizar
   - Melhorias a implementar
   - Recursos necessários

TEMPLATE DE REVISÃO:
```
REVISÃO MENSAL - [Mês/Ano]

RESULTADOS:
- Reuniões: ___/___  (___%)
- Pipeline: R$ ___
- Conversão email: ___%
- Conversão LinkedIn: ___%

TOP 3 SUCESSOS:
1.
2.
3.

TOP 3 DESAFIOS:
1.
2.
3.

APRENDIZADOS:
-
-

AÇÕES PRÓXIMO MÊS:
1.
2.
3.
```

AJUSTES COMUNS:

Mercado mudou:
- Atualizar ICP
- Novos gatilhos
- Nova proposta de valor

Resultados abaixo:
- Mais testes A/B
- Revisar lista de prospects
- Melhorar qualificação

Resultados acima:
- Documentar o que funcionou
- Escalar atividades
- Manter consistência

ENTREGÁVEIS:
- Relatório mensal
- Ações definidas
- Metas atualizadas
- Backlog de melhorias'''
            },
            {
                'ordem': 24,
                'titulo': 'Atualização de ICP e Estratégia',
                'tempo_estimado': 90,
                'descricao': '''OBJETIVO: Revisar e atualizar ICP e estratégia periodicamente.

QUANDO REVISAR:
- Trimestralmente (revisão leve)
- Semestralmente (revisão profunda)
- Quando resultados caem significativamente
- Quando mercado muda

O QUE ANALISAR:

1. CLIENTES GANHOS
   - Quem fechou nos últimos 3-6 meses
   - O que têm em comum
   - Como chegaram
   - Por que compraram

2. CLIENTES PERDIDOS
   - Quem não fechou
   - Por que não fechou
   - Eram ICP ou não

3. MELHORES CLIENTES
   - Maior ticket
   - Menor CAC
   - Maior LTV
   - Melhor fit

4. MERCADO
   - Novos segmentos
   - Mudanças econômicas
   - Novos concorrentes
   - Novas tecnologias

PERGUNTAS PARA REVISÃO:

ICP:
- O ICP atual ainda é válido?
- Devemos expandir ou focar mais?
- Novos segmentos surgiram?
- Algum segmento devemos abandonar?

Mensagem:
- A proposta de valor ainda ressoa?
- Novas dores surgiram?
- Novos benefícios a destacar?
- Cases mais recentes/relevantes?

Canais:
- Quais canais performam melhor?
- Devemos testar novos canais?
- Algum canal devemos abandonar?

ATUALIZAÇÃO DO PLAYBOOK:

A cada trimestre:
- Atualizar templates
- Adicionar novas objeções
- Incluir novos cases
- Remover o que não funciona

ENTREGÁVEIS:
- ICP revisado
- Proposta de valor atualizada
- Playbook atualizado
- Plano para próximo trimestre'''
            },
            {
                'ordem': 25,
                'titulo': 'Treinamento e Desenvolvimento',
                'tempo_estimado': 120,
                'descricao': '''OBJETIVO: Manter equipe atualizada e em desenvolvimento.

ÁREAS DE DESENVOLVIMENTO:

1. HABILIDADES DE COMUNICAÇÃO
   - Escrita persuasiva
   - Comunicação verbal
   - Escuta ativa
   - Rapport

2. CONHECIMENTO DE PRODUTO
   - Features e benefícios
   - Cases de sucesso
   - Comparativo com concorrentes
   - Roadmap

3. CONHECIMENTO DE MERCADO
   - Tendências do setor
   - Desafios comuns
   - Jargões e linguagem
   - Players principais

4. FERRAMENTAS
   - Novas funcionalidades
   - Automações
   - Otimizações

FORMATOS DE TREINAMENTO:

Semanal:
- Role play de ligações (30 min)
- Revisão de calls gravadas
- Compartilhar vitórias e aprendizados

Mensal:
- Workshop de habilidade específica
- Treinamento de produto
- Análise de métricas em grupo

Trimestral:
- Reciclagem completa
- Novos processos
- Certificações

ROLE PLAY:

Estrutura:
1. Definir cenário (cargo, empresa, objeção)
2. Um faz o SDR, outro o prospect
3. Executar por 5-10 min
4. Feedback do grupo
5. Trocar papéis

Cenários para praticar:
- Prospect apressado
- Objeção de preço
- "Já tenho fornecedor"
- Prospect interessado
- Gatekeeper

BIBLIOTECA DE RECURSOS:

Criar e manter:
- Gravações de melhores calls
- Templates que funcionam
- Artigos relevantes
- Cursos recomendados
- Podcasts do setor

MÉTRICAS DE DESENVOLVIMENTO:
- Tempo de ramp-up
- Evolução de métricas individuais
- Feedback qualitativo
- Retenção de SDRs

ENTREGÁVEIS:
- Calendário de treinamentos
- Biblioteca de recursos
- Programa de role play
- Plano de desenvolvimento individual'''
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
