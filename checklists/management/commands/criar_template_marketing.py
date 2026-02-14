"""
Comando para criar template de Marketing Digital completo com documentação
Uso: python manage.py criar_template_marketing
"""
from django.core.management.base import BaseCommand
from checklists.models import ProjetoTemplate, EtapaTemplate


class Command(BaseCommand):
    help = 'Cria template completo de Marketing Digital com todas as etapas e documentação'

    def handle(self, *args, **options):
        # Criar o template principal
        template, created = ProjetoTemplate.objects.get_or_create(
            titulo='Marketing Digital Completo',
            defaults={
                'descricao': '''Template completo para projetos de Marketing Digital.
Inclui todas as etapas desde o briefing inicial até a análise de resultados.
Canais: Facebook, Instagram, YouTube, Google Ads, TikTok, Kwai, LinkedIn Sales Navigator.

Cada etapa contém documentação detalhada de como executar.''',
                'cor': '#ec4899',  # Rosa/Magenta
                'ativo': True,
            }
        )

        if not created:
            self.stdout.write(self.style.WARNING(f'Template "{template.titulo}" já existe. Atualizando etapas...'))
            template.etapas.all().delete()
        else:
            self.stdout.write(self.style.SUCCESS(f'Template "{template.titulo}" criado!'))

        # Definir todas as etapas do marketing com documentação completa
        etapas = [
            # ========== FASE 1: DESCOBERTA E PLANEJAMENTO ==========
            {
                'ordem': 1,
                'titulo': 'Briefing Inicial com Cliente',
                'descricao': '''## OBJETIVO
Coletar todas as informações necessárias para desenvolver a estratégia de marketing digital.

## PASSO A PASSO

### 1. Preparação (30 min antes)
- [ ] Revisar informações prévias do cliente (site, redes sociais)
- [ ] Preparar questionário de briefing
- [ ] Testar link da reunião (Zoom/Meet)
- [ ] Ter documento compartilhado pronto para anotações

### 2. Durante a Reunião

#### Bloco 1: Sobre o Negócio (15 min)
- O que a empresa faz? (elevator pitch)
- Qual o diferencial competitivo?
- Quais produtos/serviços serão divulgados?
- Qual o ticket médio?
- Qual a margem de lucro?

#### Bloco 2: Objetivos (15 min)
- Qual o objetivo principal? (vendas, leads, branding)
- Qual a meta de faturamento/leads mensal?
- Em quanto tempo espera resultados?
- Qual o orçamento mensal para marketing?

#### Bloco 3: Público-Alvo (15 min)
- Quem é o cliente ideal?
- Faixa etária, gênero, localização
- Quais as dores/problemas que resolve?
- Como o cliente encontra vocês hoje?
- Quem são os concorrentes?

#### Bloco 4: Histórico (15 min)
- Já fizeram marketing digital antes?
- O que funcionou/não funcionou?
- Têm materiais (fotos, vídeos, depoimentos)?
- Têm acesso às contas de anúncios anteriores?

### 3. Pós-Reunião
- [ ] Organizar anotações em documento formal
- [ ] Enviar resumo por e-mail para cliente validar
- [ ] Solicitar acessos necessários (redes, site, etc.)
- [ ] Agendar próxima reunião de apresentação de estratégia

## ENTREGÁVEIS
- Documento de briefing preenchido
- Lista de acessos necessários
- Cronograma inicial acordado

## FERRAMENTAS
- Zoom/Google Meet para reunião
- Google Docs para anotações
- Trello/Notion para organização''',
                'tempo_estimado': 120,
            },
            {
                'ordem': 2,
                'titulo': 'Análise de Mercado e Concorrência',
                'descricao': '''## OBJETIVO
Mapear o cenário competitivo e identificar oportunidades de diferenciação.

## PASSO A PASSO

### 1. Identificar Concorrentes (1h)
- [ ] Listar 5-10 concorrentes diretos
- [ ] Listar 3-5 concorrentes indiretos
- [ ] Buscar no Google pelas palavras-chave do nicho
- [ ] Verificar quem aparece nos anúncios pagos

### 2. Análise de Redes Sociais (1h)
Para cada concorrente, analisar:

**Instagram:**
- Número de seguidores
- Média de curtidas/comentários
- Frequência de postagem
- Tipos de conteúdo que performam melhor
- Tom de voz e identidade visual
- Usar: Not Just Analytics, Social Blade

**Facebook:**
- Biblioteca de Anúncios (facebook.com/ads/library)
- Tipos de anúncios que estão rodando
- Há quanto tempo estão anunciando
- Criativos utilizados

**YouTube:**
- Número de inscritos
- Visualizações médias
- Tipos de vídeos
- Frequência de upload

### 3. Análise de SEO/Google (1h)
- [ ] Verificar posicionamento no Google
- [ ] Usar SEMrush/Ubersuggest para palavras-chave
- [ ] Analisar backlinks
- [ ] Verificar Google Ads da concorrência

### 4. Análise SWOT Digital (30 min)
Preencher matriz:

| Forças | Fraquezas |
|--------|-----------|
| O que fazem bem | Onde podem melhorar |

| Oportunidades | Ameaças |
|---------------|---------|
| Gaps no mercado | Riscos identificados |

### 5. Documentar Insights (30 min)
- [ ] O que podemos fazer diferente?
- [ ] Quais estratégias copiar (modelar)?
- [ ] Quais erros evitar?
- [ ] Oportunidades de posicionamento

## ENTREGÁVEIS
- Planilha de análise de concorrentes
- Documento de análise SWOT
- Lista de oportunidades identificadas

## FERRAMENTAS
- SEMrush / Ubersuggest / Ahrefs
- Social Blade / Not Just Analytics
- Facebook Ads Library
- SimilarWeb
- Google Trends''',
                'tempo_estimado': 240,
            },
            {
                'ordem': 3,
                'titulo': 'Definição de Personas',
                'descricao': '''## OBJETIVO
Criar perfis detalhados dos clientes ideais para direcionar toda a comunicação.

## PASSO A PASSO

### 1. Coleta de Dados (1h)
- [ ] Entrevistar cliente sobre seus melhores clientes
- [ ] Analisar dados do CRM/vendas (se houver)
- [ ] Verificar comentários e interações nas redes
- [ ] Analisar reviews e depoimentos
- [ ] Pesquisar em grupos do Facebook/comunidades

### 2. Criar Persona Principal (1h)

**Template de Persona:**

```
NOME: [Nome fictício]
IDADE: [Faixa etária]
PROFISSÃO: [Cargo/ocupação]
RENDA: [Faixa salarial]
LOCALIZAÇÃO: [Cidade/região]
ESTADO CIVIL: [Situação]

OBJETIVOS:
- O que ela quer alcançar?
- Quais são seus sonhos?

DORES/PROBLEMAS:
- O que a incomoda?
- Quais frustrações tem?
- O que já tentou e não funcionou?

OBJEÇÕES:
- Por que NÃO compraria?
- Quais medos tem?

COMPORTAMENTO ONLINE:
- Quais redes sociais usa?
- Que horas está online?
- Que tipo de conteúdo consome?
- Quem ela segue/admira?

GATILHOS DE COMPRA:
- O que a faria comprar HOJE?
- Quais palavras/promessas a atraem?

FRASE QUE ELA DIRIA:
"[Uma frase que representa seu pensamento]"
```

### 3. Criar Personas Secundárias (30 min cada)
- Repetir o processo para 1-2 personas secundárias
- Podem ser decisores diferentes (ex: quem usa vs quem paga)

### 4. Validar com Cliente (30 min)
- [ ] Apresentar personas criadas
- [ ] Ajustar com base no feedback
- [ ] Confirmar prioridade entre elas

### 5. Criar Mapa de Empatia (opcional)
```
       PENSA E SENTE
            |
OUVE ------[PERSONA]------ VÊ
            |
       FALA E FAZ
```

## ENTREGÁVEIS
- 2-3 personas documentadas
- Mapa de empatia (opcional)
- Jornada de compra por persona

## FERRAMENTAS
- Canva (template de persona)
- Google Forms (pesquisa)
- Miro/FigJam (mapa de empatia)
- HubSpot Make My Persona''',
                'tempo_estimado': 180,
            },
            {
                'ordem': 4,
                'titulo': 'Estratégia de Marketing Digital',
                'descricao': '''## OBJETIVO
Criar documento estratégico que guiará todas as ações de marketing.

## PASSO A PASSO

### 1. Definir Objetivos SMART (30 min)

**Template:**
- **S**pecific (Específico): O que exatamente?
- **M**easurable (Mensurável): Como medir?
- **A**chievable (Alcançável): É realista?
- **R**elevant (Relevante): Faz sentido para o negócio?
- **T**ime-bound (Temporal): Prazo definido?

Exemplo: "Gerar 100 leads qualificados por mês via Instagram Ads, com custo máximo de R$30 por lead, nos próximos 3 meses."

### 2. Definir Canais Prioritários (30 min)

| Canal | Objetivo | Investimento | Prioridade |
|-------|----------|--------------|------------|
| Instagram | Branding + Leads | R$ X | Alta |
| Google Ads | Conversão | R$ Y | Alta |
| TikTok | Alcance | R$ Z | Média |

### 3. Desenhar Funil de Marketing (1h)

```
TOPO (Consciência)
├── Conteúdo orgânico (Reels, posts)
├── Anúncios de alcance
└── YouTube/Blog

MEIO (Consideração)
├── E-book/Material rico
├── Remarketing
└── Email marketing

FUNDO (Decisão)
├── Oferta direta
├── Remarketing de carrinho
└── WhatsApp/Comercial
```

### 4. Definir KPIs por Etapa (30 min)

**Topo:**
- Alcance
- Impressões
- Crescimento de seguidores
- Visualizações de vídeo

**Meio:**
- Cliques
- CTR
- Leads gerados
- CPL (Custo por Lead)

**Fundo:**
- Vendas
- ROAS
- CAC (Custo de Aquisição)
- Ticket médio

### 5. Montar Calendário Macro (1h)

```
MÊS 1: Setup + Primeiras campanhas
MÊS 2: Otimização + Escala
MÊS 3: Análise + Ajustes
```

### 6. Definir Orçamento (30 min)

| Item | % do Budget | Valor |
|------|-------------|-------|
| Facebook/Instagram Ads | 40% | R$ |
| Google Ads | 30% | R$ |
| Produção de conteúdo | 20% | R$ |
| Ferramentas | 10% | R$ |

## ENTREGÁVEIS
- Documento de estratégia completo
- Apresentação para cliente
- Cronograma de implementação

## FERRAMENTAS
- Google Slides/Canva
- Miro/FigJam
- Planilha de orçamento''',
                'tempo_estimado': 240,
            },

            # ========== FASE 2: ESTRUTURAÇÃO DE CANAIS ==========
            {
                'ordem': 5,
                'titulo': 'Configuração Facebook Business',
                'descricao': '''## OBJETIVO
Configurar toda a estrutura do Facebook para gestão profissional e anúncios.

## PASSO A PASSO

### 1. Business Manager (30 min)
- [ ] Acessar business.facebook.com
- [ ] Criar conta Business Manager (se não existir)
- [ ] Adicionar página do Facebook
- [ ] Adicionar conta de anúncios
- [ ] Configurar formas de pagamento
- [ ] Adicionar membros da equipe com permissões

### 2. Configurar Página do Facebook (30 min)
- [ ] Atualizar foto de perfil (logo 180x180px)
- [ ] Atualizar capa (820x312px)
- [ ] Preencher TODAS as informações:
  - Sobre
  - Contato
  - Horário de funcionamento
  - Localização
- [ ] Adicionar botão de ação (WhatsApp/Site)
- [ ] Configurar respostas automáticas do Messenger

### 3. Instalar Pixel do Facebook (45 min)

**Via Google Tag Manager (recomendado):**
1. Acessar Gerenciador de Eventos
2. Criar novo Pixel
3. Copiar ID do Pixel
4. No GTM, criar tag "Facebook Pixel"
5. Configurar acionador "All Pages"
6. Publicar container

**Eventos a configurar:**
- PageView (automático)
- ViewContent (página de produto)
- AddToCart (adicionar ao carrinho)
- InitiateCheckout (iniciar checkout)
- Purchase (compra confirmada)
- Lead (formulário enviado)

### 4. Verificar Domínio (15 min)
- [ ] Acessar Configurações do Business
- [ ] Ir em "Brand Safety" > "Domínios"
- [ ] Adicionar domínio
- [ ] Verificar via meta tag ou DNS

### 5. Criar Públicos (30 min)

**Públicos Personalizados:**
- Visitantes do site (30, 60, 90, 180 dias)
- Engajamento Instagram (365 dias)
- Engajamento Facebook (365 dias)
- Lista de clientes (upload)
- Visualizadores de vídeo (25%, 50%, 75%, 95%)

**Públicos Lookalike:**
- Lookalike de compradores (1%, 2%, 5%)
- Lookalike de leads (1%, 2%, 5%)
- Lookalike de engajamento (1%, 2%)

### 6. Testar Pixel (15 min)
- [ ] Instalar extensão "Facebook Pixel Helper"
- [ ] Navegar pelo site verificando eventos
- [ ] Usar ferramenta de teste de eventos no Gerenciador

## ENTREGÁVEIS
- Business Manager configurado
- Pixel instalado e testado
- Públicos criados
- Checklist de configuração

## FERRAMENTAS
- Facebook Business Manager
- Google Tag Manager
- Facebook Pixel Helper (extensão Chrome)''',
                'tempo_estimado': 180,
            },
            {
                'ordem': 6,
                'titulo': 'Configuração Instagram Business',
                'descricao': '''## OBJETIVO
Otimizar perfil do Instagram para conversão e vinculá-lo ao ecossistema Meta.

## PASSO A PASSO

### 1. Converter para Conta Comercial (10 min)
- [ ] Configurações > Conta > Mudar para conta profissional
- [ ] Selecionar categoria do negócio
- [ ] Vincular à página do Facebook

### 2. Otimizar Bio (30 min)

**Estrutura ideal:**
```
[O que você faz] + [Para quem]
[Benefício principal ou diferencial]
[Prova social] (ex: +500 clientes atendidos)
[CTA] 👇
[Link]
```

**Exemplo:**
```
Marketing Digital para E-commerces 🛒
Ajudamos lojas online a vender mais com tráfego pago
+R$10M gerados para nossos clientes
Agende uma consultoria gratuita 👇
[link]
```

### 3. Configurar Linktree/Bio Link (15 min)
- [ ] Criar conta no Linktree/Beacons/Stan
- [ ] Adicionar links principais:
  - WhatsApp
  - Site
  - Produto/Serviço principal
  - Material gratuito
  - Outras redes

### 4. Criar Destaques (45 min)

**Destaques recomendados:**
1. **INÍCIO AQUI** - Apresentação da empresa
2. **SERVIÇOS** - O que oferece
3. **DEPOIMENTOS** - Prova social
4. **DÚVIDAS** - FAQ
5. **BASTIDORES** - Humanização
6. **RESULTADOS** - Cases de sucesso

**Para cada destaque:**
- Criar capa personalizada (1080x1920px, área segura)
- Selecionar stories relevantes
- Manter atualizado

### 5. Configurar Botões de Ação (10 min)
- [ ] Editar perfil > Opções de contato
- [ ] Adicionar:
  - Telefone/WhatsApp
  - E-mail
  - Endereço (se aplicável)
- [ ] Configurar botão de ação (Ligar, E-mail, Direções)

### 6. Instagram Shopping (se aplicável) (30 min)
- [ ] Ter catálogo no Facebook
- [ ] Solicitar aprovação do Shopping
- [ ] Vincular produtos
- [ ] Marcar produtos nos posts

### 7. Definir Grade Visual (20 min)
- [ ] Escolher estilo de feed (xadrez, linhas, etc.)
- [ ] Definir paleta de cores
- [ ] Criar templates no Canva
- [ ] Planejar primeiros 9-12 posts

## ENTREGÁVEIS
- Perfil otimizado
- Bio estratégica
- Destaques criados
- Link na bio configurado

## FERRAMENTAS
- Canva (templates e capas)
- Linktree/Beacons
- Preview App (planejamento de feed)''',
                'tempo_estimado': 120,
            },
            {
                'ordem': 7,
                'titulo': 'Configuração Google Ads',
                'descricao': '''## OBJETIVO
Estruturar conta do Google Ads para campanhas de pesquisa, display e YouTube.

## PASSO A PASSO

### 1. Criar/Acessar Conta (15 min)
- [ ] Acessar ads.google.com
- [ ] Criar conta (ou acessar existente)
- [ ] Configurar fuso horário (Brasil/São Paulo)
- [ ] Configurar moeda (BRL)
- [ ] Adicionar forma de pagamento

### 2. Vincular ao Google Analytics 4 (15 min)
- [ ] Ferramentas > Contas vinculadas
- [ ] Vincular propriedade do GA4
- [ ] Importar conversões do GA4
- [ ] Ativar sinais do Google

### 3. Configurar Conversões (45 min)

**Conversões principais a criar:**
1. **Compra** (valor = dinâmico)
2. **Lead/Formulário** (valor = ticket médio / taxa conversão)
3. **WhatsApp Click** (valor = estimado)
4. **Ligação** (valor = estimado)

**Via Google Tag Manager:**
1. Criar tag de conversão do Google Ads
2. Configurar ID de conversão + Label
3. Definir acionador (evento de compra/lead)
4. Publicar

### 4. Instalar Tag do Google (20 min)
- [ ] Copiar Global Site Tag
- [ ] Instalar via GTM ou direto no site
- [ ] Configurar remarketing
- [ ] Testar com Tag Assistant

### 5. Pesquisa de Palavras-Chave (1h)

**Usando o Planejador de Palavras-Chave:**
1. Ferramentas > Planejamento > Planejador de palavras-chave
2. Descobrir novas palavras-chave
3. Inserir termos do negócio
4. Analisar:
   - Volume de pesquisa
   - Concorrência
   - Lance sugerido

**Organizar em categorias:**
- Palavras de marca
- Palavras de produto/serviço
- Palavras de problema
- Palavras de solução
- Palavras de concorrentes

### 6. Criar Listas de Remarketing (30 min)

**Públicos a criar:**
- Todos os visitantes (30, 90, 180, 540 dias)
- Visitantes de páginas específicas
- Convertidos (para exclusão)
- Carrinho abandonado
- Visitantes de blog

### 7. Estruturar Conta (30 min)

```
CONTA
├── Campanha: [Marca]
│   └── Grupo: Termos de marca
├── Campanha: [Produto A]
│   ├── Grupo: Exato
│   ├── Grupo: Frase
│   └── Grupo: Ampla modificada
├── Campanha: [Produto B]
│   └── ...
├── Campanha: [Remarketing]
│   └── Grupo: Display remarketing
└── Campanha: [YouTube]
    └── Grupo: In-stream
```

## ENTREGÁVEIS
- Conta estruturada
- Conversões configuradas
- Palavras-chave pesquisadas
- Públicos de remarketing criados

## FERRAMENTAS
- Google Ads
- Google Tag Manager
- Google Tag Assistant
- Planejador de Palavras-chave
- Ubersuggest/SEMrush''',
                'tempo_estimado': 240,
            },
            {
                'ordem': 8,
                'titulo': 'Configuração YouTube',
                'descricao': '''## OBJETIVO
Criar/otimizar canal do YouTube para SEO e vincular ao Google Ads.

## PASSO A PASSO

### 1. Criar/Acessar Canal (15 min)
- [ ] Acessar YouTube Studio
- [ ] Criar canal da marca (não pessoal)
- [ ] Configurar URL personalizada (quando elegível)

### 2. Configurar Branding (45 min)

**Foto do perfil:**
- Tamanho: 800x800px
- Usar logo da empresa

**Banner:**
- Tamanho: 2560x1440px (área segura: 1546x423px)
- Incluir: logo, tagline, CTA

**Marca d'água:**
- Tamanho: 150x150px
- Logo simples e transparente
- Configurar para aparecer no final do vídeo

### 3. Preencher Informações (30 min)
- [ ] Descrição do canal (palavras-chave + links)
- [ ] Links para redes sociais
- [ ] E-mail para contato comercial
- [ ] País e palavras-chave do canal

### 4. Configurar Layout do Canal (30 min)
- [ ] Criar trailer para não-inscritos
- [ ] Definir vídeo em destaque para inscritos
- [ ] Criar seções:
  - Uploads recentes
  - Playlists populares
  - Vídeos mais vistos

### 5. Criar Playlists Estratégicas (30 min)

**Exemplos:**
- [Produto/Serviço] - Tutoriais
- [Produto/Serviço] - Dicas
- Depoimentos de Clientes
- Bastidores
- Lives/Webinars

### 6. Configurar Cards e Telas Finais (20 min)

**Cards (durante o vídeo):**
- Link para outros vídeos
- Link para playlists
- Link para site (se elegível)

**Tela final (últimos 20s):**
- Vídeo/playlist sugerido
- Inscrição no canal
- Link externo

### 7. Vincular ao Google Ads (10 min)
- [ ] YouTube Studio > Configurações > Canal > Avançado
- [ ] Vincular conta do Google Ads
- [ ] Confirmar vinculação

### 8. SEO para Vídeos - Template (20 min)

**Para cada vídeo:**
```
TÍTULO: [Palavra-chave principal] - [Benefício] | [Marca]
(máx. 60 caracteres)

DESCRIÇÃO:
[Resumo do vídeo em 2-3 linhas com palavra-chave]

🔗 LINKS IMPORTANTES:
[Site]
[WhatsApp]
[Instagram]

📌 NESTE VÍDEO:
00:00 - Introdução
01:30 - Tópico 1
03:45 - Tópico 2
...

#hashtag1 #hashtag2 #hashtag3

TAGS: palavra1, palavra2, palavra3...
```

## ENTREGÁVEIS
- Canal configurado e otimizado
- Branding aplicado
- Playlists criadas
- Template de SEO

## FERRAMENTAS
- YouTube Studio
- Canva (banners)
- TubeBuddy/VidIQ (SEO)''',
                'tempo_estimado': 180,
            },
            {
                'ordem': 9,
                'titulo': 'Configuração TikTok Business',
                'descricao': '''## OBJETIVO
Estruturar presença no TikTok e configurar TikTok Ads Manager.

## PASSO A PASSO

### 1. Criar Conta Business (15 min)
- [ ] Baixar TikTok e criar conta
- [ ] Converter para conta Business
- [ ] Selecionar categoria do negócio

### 2. Otimizar Perfil (20 min)

**Estrutura da bio:**
```
[O que você faz] [emoji]
[Para quem/benefício]
[CTA] 👇
```

- [ ] Foto de perfil (logo)
- [ ] Nome de usuário (@marca)
- [ ] Link na bio

### 3. Configurar TikTok Ads Manager (30 min)
- [ ] Acessar ads.tiktok.com
- [ ] Criar conta de anúncios
- [ ] Configurar Business Center
- [ ] Adicionar forma de pagamento
- [ ] Vincular conta TikTok

### 4. Instalar TikTok Pixel (45 min)

**Via código direto ou GTM:**
1. Acessar Ativos > Eventos
2. Criar Pixel
3. Copiar código base
4. Instalar no site (cabeçalho)
5. Configurar eventos:
   - PageView (automático)
   - ViewContent
   - AddToCart
   - InitiateCheckout
   - CompletePayment
   - SubmitForm

### 5. Pesquisar Trends do Nicho (30 min)
- [ ] Navegar na aba "Descobrir"
- [ ] Buscar hashtags do nicho
- [ ] Identificar:
  - Sons em alta
  - Formatos populares
  - Trends adaptáveis
  - Influenciadores do nicho
- [ ] Criar banco de referências

### 6. Definir Identidade Visual (20 min)
- [ ] Estilo de edição (cortes rápidos, texto na tela)
- [ ] Cores predominantes
- [ ] Fonte para textos
- [ ] Vinheta de abertura/encerramento

### 7. Criar Primeiros Vídeos de Teste (60 min)

**Formatos que funcionam:**
1. Tutorial rápido (passo a passo)
2. Antes e depois
3. Dica do dia
4. Bastidores
5. Trend adaptada ao nicho
6. Resposta a comentário
7. POV (Point of View)

**Dicas de produção:**
- Vertical (9:16)
- Gancho nos primeiros 3 segundos
- Texto na tela
- Usar sons em alta
- CTA no final

## ENTREGÁVEIS
- Conta business configurada
- Pixel instalado
- Banco de trends/referências
- 3-5 vídeos de teste

## FERRAMENTAS
- TikTok App
- TikTok Ads Manager
- CapCut (edição)
- Tokboard/Trend.io (trends)''',
                'tempo_estimado': 180,
            },
            {
                'ordem': 10,
                'titulo': 'Configuração Kwai Ads',
                'descricao': '''## OBJETIVO
Configurar Kwai for Business para anúncios (foco em público brasileiro).

## PASSO A PASSO

### 1. Criar Conta Business (15 min)
- [ ] Baixar Kwai e criar conta
- [ ] Acessar kwai.com/business
- [ ] Criar conta de anunciante
- [ ] Verificar empresa

### 2. Configurar Kwai Ads Manager (20 min)
- [ ] Acessar painel de anúncios
- [ ] Configurar dados da empresa
- [ ] Adicionar forma de pagamento
- [ ] Definir fuso horário e moeda

### 3. Instalar Pixel Kwai (30 min)

**Passos:**
1. Acessar Ferramentas > Pixel
2. Criar novo Pixel
3. Copiar código
4. Instalar via GTM ou direto
5. Configurar eventos padrão

**Eventos importantes:**
- PageView
- ViewContent
- AddToCart
- Purchase
- Register

### 4. Entender Formatos de Anúncio (20 min)

**Formatos disponíveis:**
- In-Feed Video Ads (vídeo no feed)
- Top View Ads (primeiro ao abrir)
- Hashtag Challenge (desafios)

**Especificações:**
- Formato: 9:16 (vertical)
- Duração: 5-60 segundos
- Resolução: mínimo 720p

### 5. Criar Públicos (20 min)
- [ ] Público por interesses
- [ ] Público por comportamento
- [ ] Público por localização (foco regional)
- [ ] Remarketing (visitantes do site)

### 6. Estruturar Primeira Campanha (15 min)

```
Campanha: [Objetivo]
├── Grupo: [Segmentação A]
│   └── Anúncio 1, 2, 3
└── Grupo: [Segmentação B]
    └── Anúncio 1, 2, 3
```

**Objetivos disponíveis:**
- Tráfego
- Conversões
- Instalação de App
- Alcance

## ENTREGÁVEIS
- Conta Kwai Business ativa
- Pixel instalado
- Públicos criados
- Estrutura de campanha

## FERRAMENTAS
- Kwai App
- Kwai Ads Manager
- Google Tag Manager''',
                'tempo_estimado': 120,
            },
            {
                'ordem': 11,
                'titulo': 'Configuração LinkedIn Sales Navigator',
                'descricao': '''## OBJETIVO
Configurar Sales Navigator para prospecção B2B e geração de leads qualificados.

## PASSO A PASSO

### 1. Ativar Sales Navigator (15 min)
- [ ] Acessar linkedin.com/sales
- [ ] Escolher plano (Core, Advanced, Advanced Plus)
- [ ] Ativar trial ou contratar
- [ ] Configurar preferências iniciais

### 2. Otimizar Perfil Pessoal (45 min)

**Checklist do perfil:**
- [ ] Foto profissional (fundo neutro)
- [ ] Banner personalizado
- [ ] Título otimizado: [Cargo] | [O que você faz] | [Para quem]
- [ ] Resumo com:
  - Quem você ajuda
  - Como você ajuda
  - Resultados que entrega
  - CTA (agende uma conversa)
- [ ] Experiências detalhadas
- [ ] Recomendações solicitadas
- [ ] Skills relevantes

### 3. Otimizar Página da Empresa (30 min)
- [ ] Logo e banner atualizados
- [ ] Descrição completa
- [ ] Especialidades
- [ ] Posts recentes
- [ ] Funcionários vinculados

### 4. Definir ICP no Sales Navigator (30 min)

**Critérios de busca:**
```
CARGO:
- Títulos exatos (CEO, Diretor de Marketing, etc.)
- Nível hierárquico (C-Level, VP, Diretor, Gerente)

EMPRESA:
- Tamanho (funcionários)
- Setor/Indústria
- Receita estimada
- Tecnologias utilizadas

LOCALIZAÇÃO:
- País, Estado, Cidade

OUTROS:
- Empresas que mudaram de cargo recentemente
- Empresas em crescimento
- Conexões em comum
```

### 5. Criar Listas de Leads (30 min)
- [ ] Criar lista "Hot Leads" (alta prioridade)
- [ ] Criar lista "Nurturing" (médio prazo)
- [ ] Criar lista "Empresas Target"
- [ ] Configurar alertas para atividades

### 6. Criar Templates de Mensagens (30 min)

**Template de Conexão:**
```
Olá [Nome],

Vi que você é [cargo] na [empresa] e trabalha com [área].

Atuo ajudando empresas como a sua a [benefício principal].

Adoraria conectar e trocar ideias sobre [tema relevante].

Abraço!
[Seu nome]
```

**Template de Follow-up 1:**
```
Olá [Nome], tudo bem?

Obrigado por conectar!

Percebi que a [empresa] atua com [área].
Temos ajudado empresas similares a [resultado específico].

Teria interesse em uma conversa rápida de 15 min para entender melhor seu cenário?

Abraço!
```

**Template de Follow-up 2 (conteúdo):**
```
[Nome], tudo bem?

Lembrei de você quando vi este [artigo/case/dado]:
[link]

Achei que poderia ser útil para [contexto da empresa].

Se quiser trocar uma ideia sobre isso, estou à disposição!
```

### 7. Integrar com CRM (opcional) (30 min)
- [ ] Verificar integração nativa (Salesforce, HubSpot, etc.)
- [ ] Configurar sincronização de leads
- [ ] Definir campos mapeados
- [ ] Testar fluxo

## ENTREGÁVEIS
- Sales Navigator ativo
- Perfil otimizado
- ICP definido
- Listas criadas
- Templates prontos

## FERRAMENTAS
- LinkedIn Sales Navigator
- Crystal Knows (análise de perfil)
- Vidyard (vídeos personalizados)
- HubSpot/Salesforce (CRM)''',
                'tempo_estimado': 180,
            },

            # ========== FASE 3: COLETA E GESTÃO DE DADOS ==========
            {
                'ordem': 12,
                'titulo': 'Configuração Google Analytics 4',
                'descricao': '''## OBJETIVO
Configurar GA4 para rastreamento completo do comportamento do usuário.

## PASSO A PASSO

### 1. Criar Propriedade GA4 (15 min)
- [ ] Acessar analytics.google.com
- [ ] Admin > Criar propriedade
- [ ] Selecionar GA4 (não Universal)
- [ ] Configurar nome, fuso horário, moeda

### 2. Configurar Fluxo de Dados (15 min)
- [ ] Criar fluxo de dados web
- [ ] Copiar ID de medição (G-XXXXXXXX)
- [ ] Ativar medição aprimorada:
  - Rolagens
  - Cliques de saída
  - Pesquisa no site
  - Engajamento com vídeo
  - Downloads de arquivo

### 3. Instalar Tag GA4 (20 min)

**Via GTM:**
1. Criar tag "GA4 Configuration"
2. Inserir ID de medição
3. Acionador: All Pages
4. Publicar

**Verificar instalação:**
- [ ] Usar extensão "Tag Assistant"
- [ ] Verificar em tempo real no GA4

### 4. Configurar Eventos Personalizados (45 min)

**Eventos importantes:**
```javascript
// Clique no WhatsApp
gtag('event', 'whatsapp_click', {
  'event_category': 'contact',
  'event_label': 'header_button'
});

// Formulário enviado
gtag('event', 'form_submit', {
  'event_category': 'lead',
  'form_name': 'contato'
});

// Compra
gtag('event', 'purchase', {
  'transaction_id': 'T12345',
  'value': 150.00,
  'currency': 'BRL'
});
```

### 5. Criar Conversões (15 min)
- [ ] Configurar > Eventos > Marcar como conversão:
  - purchase
  - form_submit
  - whatsapp_click
  - phone_call

### 6. Criar Públicos (30 min)

**Públicos sugeridos:**
- Compradores (purchase nos últimos 90 dias)
- Leads (form_submit nos últimos 30 dias)
- Carrinho abandonado (add_to_cart sem purchase)
- Engajados (session_duration > 2 min)
- Retornando (sessões > 2 nos últimos 30 dias)

### 7. Vincular ao Google Ads (10 min)
- [ ] Admin > Links de produtos > Google Ads
- [ ] Vincular conta
- [ ] Ativar importação de públicos
- [ ] Ativar importação de conversões

### 8. Criar Relatórios Personalizados (30 min)

**Relatórios úteis:**
1. Funil de conversão
2. Origem de tráfego x Conversão
3. Páginas mais acessadas
4. Dispositivos x Conversão
5. Jornada do usuário

### 9. Configurar Alertas (10 min)
- [ ] Biblioteca > Insights
- [ ] Criar alerta: "Queda de tráfego > 30%"
- [ ] Criar alerta: "Aumento de conversões"

## ENTREGÁVEIS
- GA4 configurado
- Eventos rastreando
- Conversões definidas
- Públicos criados
- Relatórios customizados

## FERRAMENTAS
- Google Analytics 4
- Google Tag Manager
- GA4 Debugger (extensão)''',
                'tempo_estimado': 180,
            },
            {
                'ordem': 13,
                'titulo': 'Configuração de CRM',
                'descricao': '''## OBJETIVO
Integrar todos os canais ao CRM para gestão centralizada de leads.

## PASSO A PASSO

### 1. Escolher/Acessar CRM (15 min)

**Opções populares:**
- RD Station (Brasil)
- HubSpot (gratuito até certo ponto)
- Pipedrive (foco em vendas)
- Salesforce (enterprise)
- Kommo/amoCRM (foco em WhatsApp)

### 2. Configurar Funil de Vendas (30 min)

**Etapas sugeridas:**
```
1. NOVO LEAD
   └── Ação: Primeiro contato em 5 min

2. CONTATO REALIZADO
   └── Ação: Qualificar interesse

3. QUALIFICADO
   └── Ação: Enviar proposta

4. PROPOSTA ENVIADA
   └── Ação: Follow-up em 3 dias

5. NEGOCIAÇÃO
   └── Ação: Resolver objeções

6. FECHADO-GANHO ✓
   └── Ação: Onboarding

7. FECHADO-PERDIDO ✗
   └── Ação: Motivo + Nurturing
```

### 3. Configurar Campos Personalizados (30 min)

**Campos importantes:**
- Origem do lead (Facebook, Google, Orgânico)
- Campanha (UTM)
- Produto de interesse
- Orçamento disponível
- Prazo para decisão
- Motivo de perda (se aplicável)

### 4. Integrar Formulários do Site (45 min)

**Opções:**
1. Formulário nativo do CRM
2. Webhook para CRM
3. Zapier/Make integração
4. API direta

**Testar:**
- [ ] Preencher formulário teste
- [ ] Verificar se lead chegou ao CRM
- [ ] Verificar campos preenchidos

### 5. Integrar WhatsApp (30 min)
- [ ] Conectar número ao CRM (se suportado)
- [ ] Ou usar integração via Zapier
- [ ] Configurar mensagens automáticas
- [ ] Rastrear conversas

### 6. Configurar Automações (45 min)

**Automações essenciais:**
1. Lead novo → Notificar vendedor
2. Lead novo → E-mail de boas-vindas
3. Sem interação 3 dias → Follow-up automático
4. Proposta enviada 5 dias → Lembrete
5. Lead perdido → Sequência de nurturing

### 7. Configurar Lead Scoring (30 min)

**Critérios de pontuação:**
```
PERFIL (quem é):
+20 pontos: Cargo decisor
+15 pontos: Empresa > 50 funcionários
+10 pontos: Orçamento compatível

ENGAJAMENTO (o que fez):
+10 pontos: Abriu e-mail
+15 pontos: Clicou em link
+25 pontos: Visitou página de preços
+30 pontos: Solicitou proposta
```

### 8. Criar Dashboards (30 min)

**Métricas importantes:**
- Leads novos (por período)
- Taxa de conversão por etapa
- Tempo médio no funil
- Origem com melhor conversão
- Vendedor com melhor performance

## ENTREGÁVEIS
- CRM configurado
- Funil estruturado
- Integrações funcionando
- Automações ativas
- Dashboard de vendas

## FERRAMENTAS
- CRM escolhido
- Zapier/Make (integrações)
- Google Sheets (backup)''',
                'tempo_estimado': 240,
            },
            {
                'ordem': 14,
                'titulo': 'Configuração de UTMs e Tracking',
                'descricao': '''## OBJETIVO
Criar sistema de rastreamento para atribuir resultados a cada canal.

## PASSO A PASSO

### 1. Definir Padrão de Nomenclatura (30 min)

**Estrutura UTM:**
```
?utm_source=[origem]
&utm_medium=[meio]
&utm_campaign=[campanha]
&utm_content=[conteudo]
&utm_term=[termo]
```

**Padrão sugerido (tudo minúsculo, sem acento):**
```
SOURCE:
- facebook
- instagram
- google
- tiktok
- linkedin
- email
- whatsapp

MEDIUM:
- cpc (pago)
- organic (orgânico)
- social (redes)
- email
- referral

CAMPAIGN:
- [ano][mes]_[objetivo]_[descricao]
- Ex: 202401_leads_ebook-marketing

CONTENT:
- [formato]_[variacao]
- Ex: video_depoimento-joao
- Ex: carrossel_dicas-01
```

### 2. Criar Planilha de Controle (30 min)

**Colunas:**
| Data | Canal | Campanha | URL Base | URL com UTM | Responsável |
|------|-------|----------|----------|-------------|-------------|

### 3. Gerar UTMs para Cada Canal (30 min)

**Usar Campaign URL Builder:**
- [ ] Facebook Ads
- [ ] Instagram Bio
- [ ] Instagram Stories (swipe up)
- [ ] Google Ads
- [ ] Email marketing
- [ ] WhatsApp
- [ ] LinkedIn

### 4. Configurar Encurtador (opcional) (15 min)
- [ ] Criar conta Bitly/Short.io
- [ ] Criar links curtos para cada UTM
- [ ] Organizar por campanha

### 5. Testar Rastreamento (30 min)

**Checklist de teste:**
- [ ] Acessar cada link UTM
- [ ] Verificar no GA4 tempo real
- [ ] Confirmar parâmetros corretos
- [ ] Testar conversão completa

### 6. Documentar para Equipe (15 min)
- [ ] Criar documento de padrões
- [ ] Treinar equipe
- [ ] Disponibilizar planilha modelo

## ENTREGÁVEIS
- Padrão de UTM definido
- Planilha de controle
- Links gerados e testados
- Documentação

## FERRAMENTAS
- Campaign URL Builder (Google)
- Bitly/Short.io
- Google Sheets
- GA4 (validação)''',
                'tempo_estimado': 120,
            },

            # ========== FASE 4: PRODUÇÃO DE CONTEÚDO ==========
            {
                'ordem': 15,
                'titulo': 'Criação de Identidade Visual Digital',
                'descricao': '''## OBJETIVO
Adaptar a identidade visual da marca para o ambiente digital.

## PASSO A PASSO

### 1. Revisar Brand Guidelines (1h)
- [ ] Analisar manual de marca existente
- [ ] Identificar cores principais e secundárias
- [ ] Verificar tipografias permitidas
- [ ] Analisar aplicações atuais

### 2. Adaptar Paleta de Cores (30 min)

**Definir:**
- Cor primária (botões, CTAs)
- Cor secundária (destaques)
- Cor de fundo (claro/escuro)
- Cor de texto
- Cor de alerta/erro
- Cor de sucesso

**Formatos:**
- HEX (#FFFFFF)
- RGB (255, 255, 255)

### 3. Definir Tipografia Digital (30 min)

**Fontes recomendadas (Google Fonts):**
- Títulos: [Fonte bold/display]
- Subtítulos: [Fonte medium]
- Corpo: [Fonte regular]
- CTAs: [Fonte semibold]

### 4. Criar Templates de Posts (3h)

**Instagram Feed (1080x1080px):**
- Template educativo (carrossel)
- Template de dica
- Template de citação
- Template de produto
- Template de depoimento
- Template de resultado/número

**Instagram Stories (1080x1920px):**
- Template de pergunta
- Template de enquete
- Template de dica rápida
- Template de bastidores
- Template de CTA

**Facebook (1200x630px):**
- Template de post padrão
- Template de link preview

### 5. Criar Capas de Destaque (1h)
- [ ] Ícones consistentes
- [ ] Mesmo estilo visual
- [ ] Tamanho: 1080x1920px (ou só o centro)

### 6. Criar Thumbnails YouTube (1h)
- [ ] Tamanho: 1280x720px
- [ ] Template com espaço para texto
- [ ] Rosto expressivo (se aplicável)
- [ ] Cores contrastantes

### 7. Documentar Manual Digital (1h)
- [ ] Compilar todas as definições
- [ ] Incluir exemplos de uso
- [ ] Incluir templates editáveis
- [ ] Disponibilizar para equipe

## ENTREGÁVEIS
- Paleta de cores digital
- Tipografia definida
- Templates Canva/Figma
- Capas de destaque
- Manual de aplicação

## FERRAMENTAS
- Canva Pro
- Figma
- Adobe Express
- Coolors (paleta)
- Google Fonts''',
                'tempo_estimado': 480,
            },
            {
                'ordem': 16,
                'titulo': 'Calendário Editorial Mensal',
                'descricao': '''## OBJETIVO
Planejar todo o conteúdo do mês para garantir consistência.

## PASSO A PASSO

### 1. Definir Pilares de Conteúdo (30 min)

**Exemplo de pilares:**
1. **Educativo** (40%) - Ensinar algo útil
2. **Inspiracional** (20%) - Motivar e conectar
3. **Promocional** (20%) - Vender produto/serviço
4. **Entretenimento** (10%) - Trends, humor, bastidores
5. **Engajamento** (10%) - Perguntas, enquetes

### 2. Mapear Datas Importantes (30 min)

**Verificar:**
- Feriados nacionais
- Datas comemorativas do nicho
- Lançamentos previstos
- Eventos do setor
- Black Friday, Natal, etc.

### 3. Definir Frequência por Canal (20 min)

| Canal | Frequência | Horários |
|-------|------------|----------|
| Instagram Feed | 1x/dia | 12h, 18h |
| Instagram Stories | 5-10x/dia | Ao longo do dia |
| Instagram Reels | 3-5x/semana | 19h |
| Facebook | 3-5x/semana | 12h, 19h |
| TikTok | 1-3x/dia | 18h, 21h |
| YouTube | 1-2x/semana | Terça 18h |
| LinkedIn | 3-5x/semana | 8h, 12h |

### 4. Criar Grade do Mês (1h)

**Template semanal:**
```
SEGUNDA: Educativo (carrossel)
TERÇA: Bastidores/Humanização
QUARTA: Dica rápida (Reels)
QUINTA: Depoimento/Prova social
SEXTA: Trend/Entretenimento
SÁBADO: Engajamento (enquete)
DOMINGO: Inspiracional
```

### 5. Brainstorm de Ideias (30 min)

**Para cada pilar, listar:**
- 10 temas educativos
- 5 histórias inspiracionais
- 5 formas de mostrar produto
- 5 trends adaptáveis
- 5 perguntas de engajamento

### 6. Preencher Calendário (30 min)
- [ ] Usar Notion, Trello ou Google Sheets
- [ ] Incluir: data, canal, pilar, tema, formato, legenda
- [ ] Deixar espaço para ajustes

### 7. Criar Banco de Ideias (contínuo)
- [ ] Pasta para salvar referências
- [ ] Anotar ideias que surgem
- [ ] Acompanhar concorrentes

## ENTREGÁVEIS
- Pilares definidos
- Calendário do mês
- Banco de ideias
- Frequência estabelecida

## FERRAMENTAS
- Notion/Trello/Asana
- Google Sheets
- Later/mLabs (agendamento)
- Pinterest (referências)''',
                'tempo_estimado': 180,
            },
            {
                'ordem': 17,
                'titulo': 'Produção de Conteúdo - Feed',
                'descricao': '''## OBJETIVO
Criar posts de alta qualidade para o feed do Instagram/Facebook.

## PASSO A PASSO

### 1. Preparar Pautas (1h)
- [ ] Revisar calendário editorial
- [ ] Definir posts da semana/quinzena
- [ ] Pesquisar referências para cada post

### 2. Criar Carrosséis Educativos (2h)

**Estrutura de 10 slides:**
```
1. CAPA: Título chamativo + gancho
2. PROBLEMA: Identificar a dor
3-7. CONTEÚDO: Dicas/passos/explicação
8. RESUMO: Recapitular pontos
9. CTA: O que fazer agora
10. FINAL: Salve + Compartilhe + Siga
```

**Dicas:**
- Texto grande e legível
- Uma ideia por slide
- Visual limpo
- Usar ícones/ilustrações

### 3. Criar Posts de Autoridade (1h)
- Resultados/números
- Estudos de caso
- Opiniões do setor
- Previsões/tendências

### 4. Criar Posts de Engajamento (1h)
- Enquetes
- "Isso ou aquilo"
- Perguntas abertas
- Complete a frase
- Mitos vs Verdades

### 5. Criar Posts de Venda (1h)
- Destaque de produto/serviço
- Oferta especial
- Depoimentos de clientes
- Antes e depois

### 6. Escrever Legendas (2h)

**Estrutura de legenda:**
```
🎯 GANCHO (primeira linha é crucial)

[Desenvolvimento do tema em 2-3 parágrafos]
Use quebras de linha para facilitar leitura.

💡 [Dica ou insight principal]

👉 [CTA: O que você quer que façam]

---
#hashtag1 #hashtag2 #hashtag3
(30 hashtags máximo, mix de grandes e nichadas)
```

### 7. Revisar e Aprovar
- [ ] Verificar erros de ortografia
- [ ] Conferir visual nos templates
- [ ] Testar links (se houver)
- [ ] Enviar para aprovação do cliente

## ENTREGÁVEIS
- 15-20 posts prontos (feed)
- Legendas escritas
- Hashtags definidas
- Aprovação do cliente

## FERRAMENTAS
- Canva (design)
- Preview App (visualização)
- ChatGPT (ideias de legenda)
- All Hashtag (pesquisa)''',
                'tempo_estimado': 480,
            },
            {
                'ordem': 18,
                'titulo': 'Produção de Conteúdo - Stories/Reels',
                'descricao': '''## OBJETIVO
Criar vídeos curtos e stories para engajamento diário.

## PASSO A PASSO

### 1. Planejar Stories da Semana (1h)

**Rotina diária sugerida:**
```
MANHÃ (3-4 stories):
- Bom dia + bastidores
- Dica rápida ou curiosidade
- Enquete/Pergunta

TARDE (2-3 stories):
- Conteúdo do feed (repost)
- Behind the scenes
- CTA (link, WhatsApp)

NOITE (2-3 stories):
- Reflexão do dia
- Engajamento (caixinha de perguntas)
- Encerramento
```

### 2. Criar Templates de Stories (1h)
- [ ] Template de bom dia
- [ ] Template de dica
- [ ] Template de enquete
- [ ] Template de CTA
- [ ] Template de depoimento

### 3. Produzir Reels Educativos (2h)

**Estrutura (15-30 segundos):**
```
0-3s: GANCHO (texto na tela ou fala impactante)
3-20s: CONTEÚDO (3-5 pontos rápidos)
20-25s: CTA (siga para mais)
```

**Tipos que funcionam:**
- Tutorial rápido
- 3 erros que você comete
- Como fazer X em 30 segundos
- Antes e depois
- Passo a passo

### 4. Produzir Reels de Trends (2h)
- [ ] Pesquisar áudios em alta
- [ ] Adaptar trend ao nicho
- [ ] Gravar variações
- [ ] Editar com CapCut

### 5. Produzir Reels de Bastidores (1h)
- Dia a dia da empresa
- Processo de trabalho
- Equipe
- Erros e bloopers

### 6. Editar Vídeos (2h)

**Checklist de edição:**
- [ ] Cortes rápidos (sem tempo morto)
- [ ] Texto na tela (acessibilidade)
- [ ] Música/áudio em alta
- [ ] Transições suaves
- [ ] Legenda automática
- [ ] Thumbnail atrativo

## ENTREGÁVEIS
- Templates de stories
- 10-15 Reels prontos
- Banco de stories para a semana
- Legendas e hashtags

## FERRAMENTAS
- CapCut (edição principal)
- InShot (alternativa)
- Canva (templates)
- Trending Sounds (pesquisa de áudios)
- CapCut Templates''',
                'tempo_estimado': 480,
            },
            {
                'ordem': 19,
                'titulo': 'Produção de Conteúdo - YouTube',
                'descricao': '''## OBJETIVO
Criar vídeos longos de alta qualidade para o YouTube.

## PASSO A PASSO

### 1. Planejar Vídeos do Mês (2h)
- [ ] Definir 4-8 vídeos
- [ ] Pesquisar palavras-chave (VidIQ/TubeBuddy)
- [ ] Verificar tendências de busca
- [ ] Analisar concorrentes

### 2. Escrever Roteiros (4h)

**Estrutura de roteiro:**
```
INTRODUÇÃO (30s-1min):
- Gancho/Problema
- O que vão aprender
- Por que assistir até o final

CONTEÚDO PRINCIPAL (5-15min):
- Tópico 1 [timestamp]
- Tópico 2 [timestamp]
- Tópico 3 [timestamp]
- Exemplos práticos

CONCLUSÃO (1min):
- Resumo dos pontos
- CTA (inscreva-se, comente, assista outro vídeo)
- Próximo vídeo/preview
```

### 3. Preparar Gravação (1h)
- [ ] Verificar iluminação
- [ ] Testar áudio
- [ ] Preparar cenário
- [ ] Verificar equipamentos
- [ ] Aquecer voz

### 4. Gravar Vídeos (4h)
- [ ] Gravar em blocos
- [ ] Múltiplas takes se necessário
- [ ] B-roll (imagens de apoio)
- [ ] Pausas para cortes

### 5. Editar Vídeos (4h)

**Checklist de edição:**
- [ ] Cortar erros e pausas
- [ ] Adicionar B-roll
- [ ] Inserir textos e gráficos
- [ ] Adicionar música de fundo
- [ ] Normalizar áudio
- [ ] Incluir cards e telas finais
- [ ] Exportar em 1080p ou 4K

### 6. Criar Thumbnails (1h por vídeo)

**Boas práticas:**
- Rosto expressivo
- Texto grande (3-5 palavras)
- Cores contrastantes
- Elemento de curiosidade
- Testar em tamanho pequeno

### 7. Otimizar para SEO

**Título (max 60 caracteres):**
[Palavra-chave] + [Benefício/Curiosidade]

**Descrição:**
```
[2-3 frases com palavra-chave sobre o vídeo]

🔗 LINKS:
[Site]
[WhatsApp]
[Redes sociais]

⏱️ TIMESTAMPS:
00:00 - Introdução
01:30 - Tópico 1
...

📌 SOBRE O VÍDEO:
[Parágrafo detalhado com palavras-chave]

#tag1 #tag2 #tag3
```

### 8. Agendar Publicação
- [ ] Fazer upload
- [ ] Preencher metadados
- [ ] Adicionar cards e telas finais
- [ ] Configurar thumbnail
- [ ] Agendar para melhor horário

## ENTREGÁVEIS
- 4-8 vídeos editados
- Thumbnails criados
- Títulos e descrições otimizados
- Timestamps definidos

## FERRAMENTAS
- DaVinci Resolve / Premiere / Final Cut
- TubeBuddy / VidIQ (SEO)
- Canva / Photoshop (thumbnails)
- StreamYard (se for live)''',
                'tempo_estimado': 960,
            },
            {
                'ordem': 20,
                'titulo': 'Produção de Conteúdo - TikTok/Kwai',
                'descricao': '''## OBJETIVO
Criar vídeos virais adaptados para TikTok e Kwai.

## PASSO A PASSO

### 1. Pesquisar Trends (1h diariamente)
- [ ] Navegar no "Para Você"
- [ ] Verificar aba "Descobrir"
- [ ] Anotar áudios em alta
- [ ] Salvar vídeos de referência
- [ ] Identificar formatos adaptáveis

### 2. Adaptar Trends ao Nicho (1h)

**Perguntas-guia:**
- Como posso usar esse áudio para meu nicho?
- Consigo transmitir minha mensagem nesse formato?
- Meu público vai entender/se identificar?

### 3. Produzir Conteúdo Original (2h)

**Formatos que funcionam:**
1. **POV** (Point of View)
2. **Tutorial rápido** (passo a passo)
3. **Antes e depois**
4. **Storytelling** (mini histórias)
5. **Resposta a comentário**
6. **Dueto/Stitch** com outros vídeos
7. **3 coisas que...** (listas)
8. **Mitos vs Verdades**

### 4. Gravar Vídeos (1h)

**Dicas de gravação:**
- Sempre vertical (9:16)
- Boa iluminação (luz natural ou ring light)
- Olhar para câmera
- Energia alta
- Falas curtas e diretas
- Não ter medo de regravação

### 5. Editar com CapCut (2h)

**Checklist:**
- [ ] Cortes rápidos (sem tempo morto)
- [ ] Texto na tela (sincronizado)
- [ ] Efeitos de zoom/transição
- [ ] Música/áudio trend
- [ ] Velocidade variada (0.5x, 2x)
- [ ] Filtros sutis
- [ ] Auto-captions

### 6. Escrever Legendas e Hashtags

**Legenda:**
- Curta e direta
- Gerar curiosidade
- CTA quando relevante

**Hashtags:**
- 3-5 hashtags
- Mix de gerais e nichadas
- Incluir hashtag do trend

### 7. Publicar nos Melhores Horários

**Horários sugeridos (testar):**
- 12h-14h (almoço)
- 18h-20h (fim do expediente)
- 21h-23h (noite)

**Frequência ideal:**
- TikTok: 1-3 vídeos/dia
- Kwai: 1-2 vídeos/dia

## ENTREGÁVEIS
- 15-20 vídeos TikTok
- 10-15 vídeos Kwai
- Banco de trends salvas
- Legendas e hashtags

## FERRAMENTAS
- TikTok/Kwai (gravação nativa)
- CapCut (edição)
- Tokboard (trends)
- Snaptik (download sem marca)''',
                'tempo_estimado': 360,
            },

            # ========== FASE 5: TRÁFEGO PAGO ==========
            {
                'ordem': 21,
                'titulo': 'Criação de Criativos para Ads',
                'descricao': '''## OBJETIVO
Produzir variações de anúncios para testes A/B.

## PASSO A PASSO

### 1. Definir Formatos Necessários (30 min)

**Facebook/Instagram:**
- Feed: 1080x1080 (quadrado), 1080x1350 (vertical)
- Stories: 1080x1920
- Vídeo: 15s, 30s, 60s

**Google:**
- Display: 300x250, 336x280, 728x90, 160x600
- Responsivo: várias imagens + textos

**TikTok/Kwai:**
- Vídeo vertical: 1080x1920 (9:16)

### 2. Criar Variações de Copy (1h)

**Para cada anúncio, criar 3 variações:**

**Abordagem A - Dor:**
"Cansado de [problema]? Descubra como [solução]"

**Abordagem B - Desejo:**
"Imagine [benefício]. Agora é possível com [produto]"

**Abordagem C - Prova Social:**
"+500 clientes já [resultado]. Você é o próximo?"

### 3. Produzir Imagens Estáticas (2h)

**Checklist de imagem:**
- [ ] Visual limpo e profissional
- [ ] Pouco texto (regra dos 20%)
- [ ] CTA claro
- [ ] Logo visível
- [ ] Cores da marca

**Variações a criar:**
- Com foto de produto
- Com foto de pessoa (lifestyle)
- Com ilustração/gráfico
- Com depoimento

### 4. Produzir Vídeos Curtos (3h)

**Estrutura de vídeo de anúncio:**
```
0-3s: GANCHO (problema ou promessa)
3-10s: DESENVOLVIMENTO (solução)
10-13s: PROVA (resultado ou depoimento)
13-15s: CTA (clique, saiba mais)
```

**Variações:**
- Talking head (pessoa falando)
- Demonstração de produto
- Montagem com fotos/vídeos
- Animação/motion graphics
- UGC (User Generated Content)

### 5. Criar Variações de CTA (30 min)
- Saiba mais
- Compre agora
- Cadastre-se
- Agende uma conversa
- Baixe grátis
- Começar teste

### 6. Organizar Nomenclatura (30 min)

**Padrão:**
```
[DATA]_[OBJETIVO]_[FORMATO]_[VARIACAO]
Ex: 202401_leads_video_depoimento-v1
Ex: 202401_vendas_imagem_produto-oferta
```

### 7. Documentar Testes Planejados (30 min)

| Teste | Variável | Variação A | Variação B |
|-------|----------|------------|------------|
| Copy | Headline | Dor | Benefício |
| Visual | Imagem | Produto | Lifestyle |
| CTA | Botão | Saiba mais | Compre agora |

## ENTREGÁVEIS
- 10-15 imagens estáticas
- 5-10 vídeos curtos
- 3 variações de copy
- Nomenclatura organizada
- Plano de testes A/B

## FERRAMENTAS
- Canva Pro (imagens)
- CapCut/Premiere (vídeos)
- Envato Elements (assets)
- Facebook Creative Hub (preview)''',
                'tempo_estimado': 480,
            },
            {
                'ordem': 22,
                'titulo': 'Campanha Facebook/Instagram Ads',
                'descricao': '''## OBJETIVO
Criar e lançar campanhas no Facebook/Instagram Ads.

## PASSO A PASSO

### 1. Definir Estrutura de Campanha (30 min)

**Funil recomendado:**
```
CAMPANHA 1: TOPO (Reconhecimento)
├── Objetivo: Alcance ou Reconhecimento de marca
├── Público: Interesses amplos
└── Orçamento: 20% do total

CAMPANHA 2: MEIO (Consideração)
├── Objetivo: Tráfego ou Engajamento
├── Público: Lookalike + Interesses
└── Orçamento: 40% do total

CAMPANHA 3: FUNDO (Conversão)
├── Objetivo: Conversões ou Vendas
├── Público: Remarketing + Lookalike compras
└── Orçamento: 40% do total
```

### 2. Configurar Campanha de Reconhecimento (30 min)
- [ ] Criar campanha > Reconhecimento
- [ ] Definir orçamento diário
- [ ] Criar conjunto de anúncios:
  - Público: Interesses do nicho
  - Idade e localização
  - Posicionamentos: automático
  - Otimização: Alcance
- [ ] Adicionar criativos (3-5 variações)

### 3. Configurar Campanha de Tráfego/Engajamento (45 min)
- [ ] Criar campanha > Tráfego
- [ ] Criar conjuntos de anúncios:
  - Conjunto 1: Lookalike 1% compradores
  - Conjunto 2: Lookalike 1% leads
  - Conjunto 3: Interesses específicos
- [ ] Configurar pixel e evento
- [ ] Adicionar criativos

### 4. Configurar Campanha de Conversão (45 min)
- [ ] Criar campanha > Conversões
- [ ] Selecionar evento de conversão (compra, lead)
- [ ] Criar conjuntos:
  - Conjunto 1: Remarketing site 30 dias
  - Conjunto 2: Remarketing engajamento 90 dias
  - Conjunto 3: Lookalike compradores 1%
- [ ] Configurar valor de conversão (se aplicável)
- [ ] Adicionar criativos focados em venda

### 5. Configurar Orçamento e Lances (30 min)

**Estratégias de lance:**
- **Menor custo**: Deixa Meta otimizar
- **Limite de custo**: Define custo máximo por resultado
- **ROAS mínimo**: Para e-commerce

**Orçamento:**
- Iniciar com orçamento por conjunto
- Após validar, migrar para CBO (Campaign Budget Optimization)

### 6. Configurar Exclusões (15 min)
- [ ] Excluir compradores dos últimos 30 dias
- [ ] Excluir públicos de remarketing das campanhas de topo
- [ ] Excluir localizações irrelevantes

### 7. Ativar e Monitorar (15 min)
- [ ] Revisar todas as configurações
- [ ] Ativar campanhas
- [ ] Verificar se estão entregando
- [ ] Configurar alertas de gastos

## ENTREGÁVEIS
- 3 campanhas configuradas
- Públicos segmentados
- Criativos vinculados
- Orçamentos definidos

## FERRAMENTAS
- Facebook Ads Manager
- Facebook Pixel Helper
- Facebook Analytics''',
                'tempo_estimado': 240,
            },
            {
                'ordem': 23,
                'titulo': 'Campanha Google Ads - Pesquisa',
                'descricao': '''## OBJETIVO
Criar campanhas de pesquisa para capturar demanda existente.

## PASSO A PASSO

### 1. Organizar Palavras-Chave (1h)

**Agrupar por intenção:**
```
MARCA:
- [nome da empresa]
- [nome da empresa] + serviço

PRODUTO/SERVIÇO:
- [serviço] + cidade
- melhor [serviço]
- [serviço] preço

PROBLEMA:
- como resolver [problema]
- ajuda com [problema]

COMPARAÇÃO:
- [concorrente] alternativa
- [serviço] vs [outro serviço]
```

### 2. Criar Estrutura de Campanha (30 min)

```
CAMPANHA: [Produto/Serviço A]
├── Grupo: Exatas (exact match)
│   └── [serviço], [serviço cidade]
├── Grupo: Frase (phrase match)
│   └── "serviço", "melhor serviço"
└── Grupo: Ampla (broad match)
    └── +serviço +cidade

CAMPANHA: [Marca]
└── Grupo: Termos de marca
    └── [nome empresa], [variações]
```

### 3. Criar Anúncios Responsivos (1h)

**Para cada grupo, criar:**
- 15 títulos (máx 30 caracteres cada)
- 4 descrições (máx 90 caracteres cada)

**Dicas:**
- Incluir palavra-chave nos títulos
- Incluir benefícios
- Incluir números/dados
- Incluir CTA
- Variar abordagens

**Exemplo:**
```
TÍTULOS:
1. [Serviço] em [Cidade]
2. Especialistas em [Serviço]
3. Orçamento Grátis | [Serviço]
4. Mais de 500 Clientes Satisfeitos
5. [Serviço] com Garantia
...

DESCRIÇÕES:
1. Solicite um orçamento gratuito hoje mesmo. Atendimento rápido e profissional.
2. Empresa líder em [serviço]. Mais de 10 anos de experiência no mercado.
...
```

### 4. Configurar Extensões (30 min)

**Extensões importantes:**
- **Sitelinks**: Páginas importantes do site
- **Frases de destaque**: Benefícios curtos
- **Snippets estruturados**: Serviços, tipos
- **Chamada**: Número de telefone
- **Local**: Endereço (se aplicável)
- **Preço**: Produtos com valores

### 5. Definir Palavras Negativas (30 min)

**Lista inicial:**
```
gratis
gratuito
como fazer
diy
curso
vagas
emprego
salario
wikipedia
o que é (dependendo do caso)
```

### 6. Configurar Lances e Orçamento (30 min)

**Estratégias recomendadas:**
- **Início**: Maximizar cliques (aprendizado)
- **Após dados**: Maximizar conversões
- **Com volume**: CPA desejado ou ROAS

### 7. Ativar e Monitorar
- [ ] Revisar configurações
- [ ] Verificar tracking
- [ ] Ativar campanhas
- [ ] Monitorar primeiras horas

## ENTREGÁVEIS
- Campanhas de pesquisa ativas
- Palavras-chave organizadas
- Anúncios responsivos criados
- Extensões configuradas
- Lista de negativas

## FERRAMENTAS
- Google Ads
- Keyword Planner
- Google Ads Editor (bulk)''',
                'tempo_estimado': 240,
            },
            {
                'ordem': 24,
                'titulo': 'Campanha Google Ads - Display/YouTube',
                'descricao': '''## OBJETIVO
Criar campanhas de display e YouTube para alcance e remarketing.

## PASSO A PASSO

### 1. Campanha de Display - Remarketing (1h)

**Configuração:**
- [ ] Criar campanha > Display
- [ ] Objetivo: Vendas ou Leads
- [ ] Segmentação: Públicos de remarketing
  - Visitantes do site (30, 60, 90 dias)
  - Abandonos de carrinho
  - Visualizadores de produto

**Criativos responsivos:**
- Imagens: 1200x628, 300x250, 160x600
- Logos: 1200x1200, 1200x300
- Títulos: 5 variações (30 caracteres)
- Descrições: 5 variações (90 caracteres)

### 2. Campanha de Display - Prospecção (1h)

**Configuração:**
- [ ] Criar campanha > Display
- [ ] Objetivo: Reconhecimento
- [ ] Segmentação:
  - Públicos de afinidade (interesses)
  - Públicos no mercado (intenção de compra)
  - Públicos personalizados (palavras-chave, URLs)

### 3. Campanha YouTube - In-Stream (1h)

**Tipos de anúncio:**
- **In-stream pulável**: Pula após 5s
- **In-stream não pulável**: 15s obrigatório
- **Bumper**: 6s não pulável

**Configuração:**
- [ ] Criar campanha > Vídeo
- [ ] Objetivo: Reconhecimento ou Conversões
- [ ] Formato: In-stream pulável (recomendado)
- [ ] Segmentação:
  - Canais específicos (placement)
  - Palavras-chave
  - Tópicos relacionados
  - Públicos de remarketing

### 4. Campanha YouTube - Discovery (30 min)

**Onde aparece:**
- Resultados de busca do YouTube
- Vídeos relacionados
- Home do YouTube

**Configuração:**
- [ ] Formato: Video Discovery
- [ ] Criar thumbnail atrativo
- [ ] Título chamativo

### 5. Configurar Públicos de Vídeo (30 min)

**Criar públicos:**
- Visualizaram qualquer vídeo
- Visualizaram vídeos específicos
- Inscritos no canal
- Visitaram canal

### 6. Otimizar Posicionamentos (30 min)
- [ ] Excluir apps e jogos (se irrelevante)
- [ ] Excluir canais de baixa qualidade
- [ ] Focar em posicionamentos relevantes

## ENTREGÁVEIS
- Campanha Display remarketing
- Campanha Display prospecção
- Campanha YouTube in-stream
- Campanha YouTube discovery
- Públicos configurados

## FERRAMENTAS
- Google Ads
- Google Ads Editor
- YouTube Studio''',
                'tempo_estimado': 240,
            },
            {
                'ordem': 25,
                'titulo': 'Campanha TikTok Ads',
                'descricao': '''## OBJETIVO
Criar campanhas no TikTok Ads Manager.

## PASSO A PASSO

### 1. Definir Estrutura (30 min)

```
CAMPANHA 1: ALCANCE
├── Objetivo: Reach
├── Público: Amplo (interesses)
└── Orçamento: 30%

CAMPANHA 2: TRÁFEGO
├── Objetivo: Traffic
├── Público: Interesses específicos
└── Orçamento: 30%

CAMPANHA 3: CONVERSÃO
├── Objetivo: Conversions
├── Público: Lookalike + Remarketing
└── Orçamento: 40%
```

### 2. Configurar Campanha de Alcance (30 min)
- [ ] Criar campanha > Reach
- [ ] Orçamento: Diário ou Total
- [ ] Criar grupo de anúncios:
  - Localização
  - Idade e gênero
  - Interesses (amplos)
  - Dispositivos
- [ ] Adicionar vídeos (nativos)

### 3. Configurar Campanha de Tráfego (30 min)
- [ ] Criar campanha > Traffic
- [ ] URL de destino
- [ ] Criar grupos:
  - Grupo 1: Interesse A
  - Grupo 2: Interesse B
  - Grupo 3: Comportamento
- [ ] Adicionar vídeos variados

### 4. Configurar Campanha de Conversão (30 min)
- [ ] Criar campanha > Conversions
- [ ] Selecionar evento do Pixel
- [ ] Criar grupos:
  - Remarketing (visitantes site)
  - Lookalike de compradores
  - Custom Audience (lista)
- [ ] Adicionar vídeos com CTA forte

### 5. Configurar Spark Ads (30 min)

**O que é:**
Impulsionar posts orgânicos (seus ou de criadores).

**Como configurar:**
- [ ] Solicitar código de autorização do post
- [ ] Inserir no TikTok Ads Manager
- [ ] Configurar campanha normalmente
- [ ] Engajamentos ficam no post original

### 6. Otimizar Criativos para TikTok (30 min)

**Boas práticas:**
- Parecer nativo (não "propaganda")
- Gancho em 1-2 segundos
- Áudio em alta
- Texto na tela
- Vertical (9:16)
- Sem bordas ou logos grandes

## ENTREGÁVEIS
- Campanha de alcance
- Campanha de tráfego
- Campanha de conversão
- Spark Ads configurados

## FERRAMENTAS
- TikTok Ads Manager
- TikTok Creative Center
- CapCut''',
                'tempo_estimado': 180,
            },
            {
                'ordem': 26,
                'titulo': 'Campanha Kwai Ads',
                'descricao': '''## OBJETIVO
Configurar campanhas no Kwai Ads para público brasileiro.

## PASSO A PASSO

### 1. Entender o Público Kwai (20 min)

**Perfil do usuário Kwai:**
- Majoritariamente classe C e D
- Forte presença no Norte e Nordeste
- Faixa etária mais ampla (incluindo 35+)
- Alto engajamento com humor e entretenimento

### 2. Configurar Campanha de Alcance (30 min)
- [ ] Criar campanha
- [ ] Objetivo: Brand Awareness
- [ ] Segmentação:
  - Regiões prioritárias
  - Interesses relevantes
  - Idade compatível
- [ ] Adicionar vídeos

### 3. Configurar Campanha de Conversão (30 min)
- [ ] Criar campanha
- [ ] Objetivo: Conversions
- [ ] Evento do Pixel
- [ ] Segmentação mais refinada
- [ ] CTA claro

### 4. Adaptar Criativos (30 min)

**Diferenças para TikTok:**
- Tom pode ser mais popular/acessível
- Humor funciona muito bem
- Preços e ofertas diretas
- CTAs mais explícitos

### 5. Monitorar e Ajustar (10 min)
- [ ] Verificar entrega
- [ ] Comparar CPM/CPC com TikTok
- [ ] Ajustar orçamento conforme performance

## ENTREGÁVEIS
- Campanha de alcance ativa
- Campanha de conversão ativa
- Criativos adaptados

## FERRAMENTAS
- Kwai Ads Manager''',
                'tempo_estimado': 120,
            },

            # ========== FASE 6: PROSPECÇÃO ATIVA ==========
            {
                'ordem': 27,
                'titulo': 'Prospecção LinkedIn Sales Navigator',
                'descricao': '''## OBJETIVO
Executar processo de prospecção ativa via LinkedIn.

## PASSO A PASSO

### 1. Rotina Diária de Prospecção (30 min/dia)

**Manhã:**
- [ ] Verificar alertas de leads
- [ ] Revisar visualizações de perfil
- [ ] Checar aceitações de conexão
- [ ] Responder mensagens

### 2. Buscar Novos Leads (20 min/dia)
- [ ] Usar filtros do Sales Navigator
- [ ] Salvar leads promissores
- [ ] Adicionar à lista correta
- [ ] Anotar informações relevantes

### 3. Enviar Solicitações de Conexão (10 min/dia)

**Limite diário:** 20-30 conexões

**Template com personalização:**
```
Olá [Nome],

Vi que você lidera [área] na [Empresa] e me chamou atenção [algo específico que você notou no perfil/empresa].

Trabalho com [sua área] e tenho ajudado empresas similares a [benefício].

Adoraria conectar!

Abraço,
[Seu nome]
```

### 4. Sequência de Mensagens

**Dia 1 (após aceitar):**
```
[Nome], obrigado por conectar!

Vi que a [Empresa] atua com [área]. Como está esse mercado para vocês?

Pergunto porque temos ajudado empresas do setor a [resultado específico].

Abraço!
```

**Dia 4 (se não respondeu):**
```
[Nome], tudo bem?

Sei que a rotina é corrida, mas queria compartilhar um [case/artigo/insight] que pode ser útil:

[Link ou resumo]

Se tiver interesse em conversar sobre como aplicar isso na [Empresa], estou à disposição!
```

**Dia 7 (última tentativa):**
```
[Nome], última mensagem por aqui!

Caso faça sentido uma conversa de 15 min para entender seu cenário e ver se podemos ajudar, só me avisar.

Se não for o momento, sem problemas! Fico por aqui caso precise no futuro.

Sucesso! 🚀
```

### 5. Registrar no CRM (5 min/dia)
- [ ] Atualizar status de cada lead
- [ ] Registrar interações
- [ ] Agendar follow-ups
- [ ] Mover no funil

### 6. Métricas Semanais

| Métrica | Meta |
|---------|------|
| Conexões enviadas | 100-150 |
| Taxa de aceitação | >30% |
| Mensagens enviadas | 50-100 |
| Taxa de resposta | >20% |
| Reuniões agendadas | 5-10 |

## ENTREGÁVEIS
- Leads prospectados
- Conexões estabelecidas
- Reuniões agendadas
- CRM atualizado

## FERRAMENTAS
- LinkedIn Sales Navigator
- CRM integrado
- Calendly (agendamento)''',
                'tempo_estimado': 480,
            },
            {
                'ordem': 28,
                'titulo': 'Coleta de Dados e Leads',
                'descricao': '''## OBJETIVO
Enriquecer base de leads e garantir compliance com LGPD.

## PASSO A PASSO

### 1. Identificar Fontes de Dados (1h)

**Fontes legítimas:**
- Formulários do site (opt-in)
- Landing pages
- Eventos/webinars
- LinkedIn (com consentimento)
- Parcerias (co-marketing)
- Indicações de clientes

### 2. Configurar Coleta (1h)

**Campos essenciais:**
- Nome completo
- E-mail
- Telefone (opcional)
- Empresa
- Cargo
- Interesse (qual produto/serviço)
- Consentimento LGPD ✓

### 3. Validar E-mails (30 min)

**Usar ferramenta de validação:**
- Remover e-mails inválidos
- Remover catch-all suspeitos
- Verificar domínios corporativos

**Ferramentas:**
- NeverBounce
- ZeroBounce
- Hunter.io

### 4. Enriquecer Dados (1h)

**Dados adicionais úteis:**
- Porte da empresa
- Faturamento estimado
- Tecnologias utilizadas
- Redes sociais
- Decisores

**Ferramentas:**
- Clearbit
- Apollo.io
- Lusha

### 5. Segmentar Base (30 min)

**Critérios de segmentação:**
- Temperatura (quente, morno, frio)
- Porte da empresa
- Setor/indústria
- Estágio no funil
- Interesse demonstrado

### 6. Garantir Compliance LGPD (30 min)

**Checklist:**
- [ ] Consentimento claro e específico
- [ ] Finalidade informada
- [ ] Opção de descadastro
- [ ] Política de privacidade atualizada
- [ ] Registro de consentimento
- [ ] Prazo de retenção definido

### 7. Importar para CRM (30 min)
- [ ] Formatar planilha
- [ ] Mapear campos
- [ ] Importar em lotes
- [ ] Verificar duplicatas
- [ ] Atribuir a vendedores

## ENTREGÁVEIS
- Base de leads validada
- Dados enriquecidos
- Segmentação aplicada
- Compliance LGPD

## FERRAMENTAS
- NeverBounce/ZeroBounce
- Apollo.io/Clearbit
- Google Sheets
- CRM''',
                'tempo_estimado': 240,
            },

            # ========== FASE 7: ANÁLISE E OTIMIZAÇÃO ==========
            {
                'ordem': 29,
                'titulo': 'Relatório Semanal de Performance',
                'descricao': '''## OBJETIVO
Analisar resultados da semana e identificar otimizações.

## PASSO A PASSO

### 1. Coletar Dados (30 min)

**Fontes:**
- Facebook Ads Manager
- Google Ads
- Google Analytics
- TikTok Ads
- CRM

### 2. Preencher Relatório

**Template:**
```
RELATÓRIO SEMANAL - [Data]

📊 RESUMO EXECUTIVO
- Investimento total: R$ X
- Leads gerados: X
- CPL médio: R$ X
- Vendas: X
- ROAS: X

📱 REDES SOCIAIS (Orgânico)
- Seguidores: +X
- Alcance: X
- Engajamento: X%
- Melhores posts: [listar]

💰 FACEBOOK/INSTAGRAM ADS
- Investido: R$ X
- Impressões: X
- Cliques: X
- CTR: X%
- Leads: X
- CPL: R$ X
- Melhor anúncio: [identificar]
- Pior anúncio: [identificar]

🔍 GOOGLE ADS
- Investido: R$ X
- Impressões: X
- Cliques: X
- CTR: X%
- Conversões: X
- CPA: R$ X
- Melhores palavras: [listar]

📈 SITE/LANDING PAGE
- Visitantes: X
- Taxa de conversão: X%
- Páginas mais acessadas: [listar]
- Taxa de rejeição: X%

💡 INSIGHTS DA SEMANA
1. [Insight 1]
2. [Insight 2]
3. [Insight 3]

✅ AÇÕES PARA PRÓXIMA SEMANA
1. [Ação 1]
2. [Ação 2]
3. [Ação 3]
```

### 3. Analisar Tendências (30 min)
- Comparar com semana anterior
- Identificar padrões
- Verificar sazonalidades

### 4. Listar Otimizações (30 min)
- O que escalar?
- O que pausar?
- O que testar?

### 5. Enviar para Cliente/Equipe (15 min)
- [ ] Revisar relatório
- [ ] Formatar apresentação
- [ ] Enviar por e-mail/WhatsApp
- [ ] Agendar call se necessário

## ENTREGÁVEIS
- Relatório semanal completo
- Lista de ações
- Apresentação (se aplicável)

## FERRAMENTAS
- Google Sheets/Data Studio
- Canva (apresentação)
- Loom (vídeo explicativo)''',
                'tempo_estimado': 120,
            },
            {
                'ordem': 30,
                'titulo': 'Otimização de Campanhas',
                'descricao': '''## OBJETIVO
Melhorar performance das campanhas com base nos dados.

## PASSO A PASSO

### 1. Analisar Métricas-Chave (30 min)

**Por campanha, verificar:**
- CTR (Click-through rate)
- CPC (Custo por clique)
- CPL (Custo por lead)
- Taxa de conversão
- ROAS (Retorno sobre investimento)
- Frequência (saturação)

### 2. Pausar Baixa Performance (30 min)

**Critérios para pausar:**
- CTR < 0.5% (imagem/copy não funciona)
- CPL 3x acima da média
- Frequência > 3 (saturação)
- Zero conversões após X gastos

### 3. Escalar Alta Performance (30 min)

**Como escalar:**
- Aumentar orçamento gradualmente (20-30%/dia)
- Duplicar para novos públicos
- Criar lookalike do público vencedor
- Expandir posicionamentos

### 4. Testar Novos Criativos (30 min)

**Variáveis para testar:**
- Headlines diferentes
- Imagens/vídeos novos
- CTAs alternativos
- Formatos diferentes

**Regra: Manter 70% do que funciona, testar 30% de novo**

### 5. Otimizar Públicos (30 min)

**Ações:**
- Refinar interesses
- Excluir públicos que não convertem
- Criar novos lookalikes
- Ajustar idade/gênero/localização

### 6. Ajustar Lances/Orçamento (30 min)

**Facebook/Instagram:**
- Mover para CBO se conjuntos performam similar
- Ajustar limite de custo

**Google:**
- Revisar estratégia de lance
- Ajustar CPA/ROAS alvo

### 7. Atualizar Negativos (15 min)

**Google Ads:**
- Adicionar termos de busca irrelevantes às negativas
- Revisar relatório de termos semanalmente

### 8. Documentar Aprendizados (15 min)
- O que funcionou?
- O que não funcionou?
- Hipóteses para próximos testes

## ENTREGÁVEIS
- Campanhas otimizadas
- Anúncios ruins pausados
- Novos testes iniciados
- Documentação atualizada

## FERRAMENTAS
- Ads Managers
- Planilha de controle''',
                'tempo_estimado': 180,
            },
            {
                'ordem': 31,
                'titulo': 'Relatório Mensal Completo',
                'descricao': '''## OBJETIVO
Criar análise completa do mês para apresentar ao cliente.

## PASSO A PASSO

### 1. Compilar Dados do Mês (1h)

**Exportar de:**
- Facebook Ads Manager
- Google Ads
- Google Analytics 4
- TikTok Ads
- CRM
- Redes sociais (orgânico)

### 2. Criar Relatório

**Estrutura do relatório:**

```
RELATÓRIO MENSAL - [Mês/Ano]
[Nome do Cliente]

1. RESUMO EXECUTIVO
   - Destaques do mês
   - Principais conquistas
   - Desafios enfrentados

2. VISÃO GERAL DE INVESTIMENTO
   | Canal | Investido | Resultado | ROI |
   |-------|-----------|-----------|-----|
   | Facebook | R$ | Leads/Vendas | X% |
   | Google | R$ | Leads/Vendas | X% |
   | Total | R$ | Total | X% |

3. PERFORMANCE POR CANAL

   3.1 FACEBOOK/INSTAGRAM ADS
   - Investimento: R$
   - Impressões: X
   - Cliques: X
   - CTR: X%
   - Leads: X
   - CPL: R$
   - Melhores campanhas/anúncios
   - Gráficos de evolução

   3.2 GOOGLE ADS
   - [mesma estrutura]

   3.3 TIKTOK/KWAI
   - [mesma estrutura]

4. REDES SOCIAIS (ORGÂNICO)
   - Crescimento de seguidores
   - Engajamento
   - Melhores conteúdos
   - Comparativo mês anterior

5. SITE/LANDING PAGES
   - Visitantes
   - Taxa de conversão
   - Origem do tráfego
   - Comportamento do usuário

6. FUNIL DE VENDAS
   - Leads totais
   - Leads qualificados
   - Oportunidades
   - Vendas fechadas
   - Taxa de conversão por etapa

7. COMPARATIVO
   - vs. Mês anterior
   - vs. Meta estabelecida
   - Evolução histórica (gráfico)

8. APRENDIZADOS DO MÊS
   - O que funcionou
   - O que não funcionou
   - Testes realizados
   - Insights de mercado

9. PLANO PARA PRÓXIMO MÊS
   - Objetivos
   - Estratégias
   - Testes planejados
   - Orçamento sugerido

10. ANEXOS
    - Prints de melhores resultados
    - Gráficos detalhados
```

### 3. Criar Visualizações (1h)
- Gráficos de evolução
- Comparativos
- Funis visuais
- Mapas de calor (se aplicável)

### 4. Preparar Apresentação (1h)
- Versão executiva (10-15 slides)
- Destaques visuais
- Storytelling dos dados

### 5. Revisar e Finalizar (30 min)
- Verificar números
- Corrigir erros
- Alinhar com equipe

## ENTREGÁVEIS
- Relatório completo (PDF)
- Apresentação executiva
- Planilha com dados brutos
- Recomendações documentadas

## FERRAMENTAS
- Google Data Studio / Looker Studio
- Google Slides / Canva
- Google Sheets
- Loom (vídeo resumo)''',
                'tempo_estimado': 240,
            },
            {
                'ordem': 32,
                'titulo': 'Reunião de Alinhamento com Cliente',
                'descricao': '''## OBJETIVO
Apresentar resultados e alinhar próximos passos com o cliente.

## PASSO A PASSO

### 1. Preparação (15 min antes)
- [ ] Revisar relatório
- [ ] Preparar pauta
- [ ] Testar apresentação
- [ ] Verificar link da reunião
- [ ] Ter métricas principais na ponta da língua

### 2. Abertura (5 min)
- Agradecer a presença
- Apresentar pauta
- Confirmar tempo disponível

### 3. Apresentar Resultados (20 min)

**Estrutura:**
1. **Destaques** - O que foi bom
2. **Desafios** - O que enfrentamos
3. **Números** - Dados principais
4. **Insights** - O que aprendemos

**Dicas:**
- Começar pelo positivo
- Ser transparente sobre problemas
- Contextualizar os números
- Comparar com metas/expectativas

### 4. Colher Feedback (15 min)

**Perguntas:**
- O que achou dos resultados?
- Está alinhado com a percepção de vocês?
- Houve mudanças no negócio que devemos saber?
- Algum feedback sobre o trabalho?

### 5. Alinhar Próximo Mês (15 min)

**Discutir:**
- Manter estratégia ou ajustar?
- Orçamento para o próximo mês
- Novos produtos/promoções
- Datas importantes
- Expectativas de resultado

### 6. Encerramento (5 min)
- Resumir acordos
- Confirmar próximos passos
- Agendar próxima reunião
- Agradecer

### 7. Pós-Reunião
- [ ] Enviar ata por e-mail
- [ ] Registrar acordos no sistema
- [ ] Atualizar cronograma
- [ ] Comunicar equipe sobre mudanças

## ENTREGÁVEIS
- Reunião realizada
- Ata enviada
- Alinhamento documentado
- Próximos passos definidos

## FERRAMENTAS
- Zoom / Google Meet
- Google Slides (apresentação)
- Notion/Google Docs (ata)''',
                'tempo_estimado': 60,
            },
        ]

        # Criar todas as etapas
        for etapa_data in etapas:
            EtapaTemplate.objects.create(
                template=template,
                **etapa_data
            )
            self.stdout.write(f'  + Etapa {etapa_data["ordem"]}: {etapa_data["titulo"]}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Template criado com {len(etapas)} etapas com documentação completa!'))
        self.stdout.write('')
        self.stdout.write('Para usar:')
        self.stdout.write('1. Acesse o sistema')
        self.stdout.write('2. Vá em Projetos > Novo Projeto')
        self.stdout.write('3. Selecione o template "Marketing Digital Completo"')
        self.stdout.write('4. Defina o cliente e dias por etapa')
        self.stdout.write('')
