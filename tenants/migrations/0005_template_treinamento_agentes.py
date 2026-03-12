"""
Data migration: Cria o Template Global "Treinamento de Agentes IA - Neuraxo Agents"
com todas as etapas passo a passo das 5 fases, incluindo guias explicativos detalhados.
"""
from django.db import migrations


ETAPAS = [
    # ============================================
    # FASE 1: CONFIGURAÇÃO BASE
    # ============================================
    {
        'ordem': 1,
        'titulo': '📋 FASE 1: CONFIGURAÇÃO BASE',
        'descricao': (
            'Nesta fase você vai configurar tudo que o agente precisa saber sobre a empresa.\n'
            'Pense nisso como o "onboarding" do agente - assim como um funcionário novo precisa\n'
            'conhecer a empresa antes de atender clientes, o agente também precisa.\n\n'
            'O QUE SERÁ FEITO:\n'
            '• Cadastrar dados da empresa (nome, contato, logo)\n'
            '• Definir horários de atendimento\n'
            '• Configurar regras de negócio (frete, troca, pagamento)\n'
            '• Criar o agente com personalidade e tom de voz\n'
            '• Configurar quando escalar para humano\n\n'
            'TEMPO ESTIMADO: ~50 minutos\n\n'
            'DICA: Tenha em mãos os dados comerciais da empresa antes de começar.\n'
            'Quanto mais completas as informações, melhor o agente vai atender.'
        ),
        'tempo_estimado': 0,
    },

    # 1.1 Dados da Empresa
    {
        'ordem': 2,
        'titulo': '1.1 - Cadastrar dados da empresa',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'O agente vai representar a empresa nas conversas. Ele precisa saber o nome correto,\n'
            'ter o logo para identificação visual e conhecer os canais de contato.\n\n'
            'COMO FAZER:\n'
            'Acesse o painel do Neuraxo Agents e preencha cada campo:\n\n'
            '1. NOME DA EMPRESA\n'
            '   Use o nome comercial (como o cliente conhece).\n'
            '   Exemplo: "Tarragona Store" (não "Tarragona Comércio de Roupas LTDA")\n\n'
            '2. CNPJ\n'
            '   Formato: XX.XXX.XXX/0001-XX\n'
            '   O agente pode precisar informar em situações de troca/nota fiscal.\n\n'
            '3. LOGO\n'
            '   Envie uma imagem PNG ou JPG com no mínimo 200x200 pixels.\n'
            '   Será usado no chat widget e relatórios.\n'
            '   Dica: Use fundo transparente (PNG) para melhor resultado.\n\n'
            '4. SITE/URL DA LOJA\n'
            '   URL completa com https://\n'
            '   Exemplo: https://www.tarragonastore.com.br\n'
            '   O agente vai enviar links de produtos para os clientes.\n\n'
            '5. WHATSAPP PRINCIPAL\n'
            '   Formato internacional: código do país + DDD + número\n'
            '   Exemplo: 5511999999999 (55 = Brasil, 11 = SP, 999999999 = número)\n'
            '   ATENÇÃO: Este é o número que VAI RECEBER as conversas dos clientes.\n'
            '   Certifique-se que é um número com WhatsApp Business ativo.\n\n'
            '6. EMAIL DE CONTATO\n'
            '   Email para onde o agente pode direcionar clientes quando necessário.\n'
            '   Exemplo: contato@tarragonastore.com.br\n\n'
            '7. SEGMENTO/NICHO\n'
            '   Escolha o segmento que mais se aproxima do seu negócio:\n'
            '   • Moda e Vestuário - roupas, calçados, acessórios\n'
            '   • Eletrônicos - celulares, notebooks, gadgets\n'
            '   • Casa e Decoração - móveis, decoração, utilidades\n'
            '   • Saúde e Beleza - cosméticos, suplementos, farmácia\n'
            '   • Alimentos e Bebidas - comida, bebidas, gourmet\n'
            '   • Esportes e Fitness - equipamentos, roupas esportivas\n'
            '   • Pet Shop - produtos para animais\n'
            '   • Infantil - brinquedos, roupas infantis\n'
            '   • Outro\n\n'
            '   Isso ajuda o agente a usar vocabulário adequado ao seu mercado.'
        ),
        'tempo_estimado': 10,
    },

    # 1.2 Horário de Atendimento
    {
        'ordem': 3,
        'titulo': '1.2 - Definir horário de atendimento',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'O agente precisa saber quando atender e o que fazer fora do horário.\n'
            'Clientes que recebem resposta fora do horário podem criar expectativas erradas.\n\n'
            'COMO FAZER:\n\n'
            '1. HORÁRIO SEGUNDA A SEXTA\n'
            '   Defina o início e fim do expediente.\n'
            '   Exemplo: 09:00 às 18:00\n'
            '   Dica: Se sua equipe atende em horários diferentes, use o horário mais amplo.\n\n'
            '2. SÁBADOS\n'
            '   Marque "Sim" se atende aos sábados e defina o horário.\n'
            '   Exemplo: 09:00 às 13:00\n'
            '   Comum no varejo: meio expediente aos sábados.\n\n'
            '3. DOMINGOS E FERIADOS\n'
            '   Na maioria dos e-commerces, não há atendimento.\n'
            '   Se sua loja atende 24/7, marque "Sim".\n\n'
            '4. COMPORTAMENTO FORA DO HORÁRIO\n'
            '   Escolha o que o agente faz quando recebe mensagem fora do expediente:\n\n'
            '   • MENSAGEM DE AUSÊNCIA (mais comum)\n'
            '     O agente responde algo como: "Olá! Nosso horário de atendimento é de\n'
            '     segunda a sexta, das 9h às 18h. Retornaremos assim que possível!"\n\n'
            '   • COLETAR DADOS\n'
            '     O agente coleta nome, email e pergunta do cliente, e avisa que vai\n'
            '     responder no próximo dia útil. Bom para não perder leads.\n\n'
            '   • ATENDER LIMITADO (FAQ)\n'
            '     O agente responde apenas perguntas básicas (horário, endereço, FAQ)\n'
            '     mas não faz vendas nem resolve problemas complexos.\n\n'
            '   • NÃO RESPONDER\n'
            '     O agente fica totalmente inativo. A mensagem fica sem resposta\n'
            '     até o próximo dia útil. Não recomendado - pode frustrar clientes.\n\n'
            'RECOMENDAÇÃO: Use "Mensagem de Ausência" ou "Coletar Dados".\n'
            'Clientes valorizam saber que foram ouvidos, mesmo fora do horário.'
        ),
        'tempo_estimado': 5,
    },

    # 1.3 Regras de Negócio
    {
        'ordem': 4,
        'titulo': '1.3 - Configurar regras de negócio',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'Estas são as informações que os clientes mais perguntam: frete, parcelamento,\n'
            'troca, desconto. Se o agente não souber, vai inventar ou escalar toda hora.\n\n'
            'COMO FAZER:\n'
            'Preencha cada campo com os valores reais da sua empresa:\n\n'
            '1. FRETE GRÁTIS ACIMA DE R$ ___\n'
            '   Valor mínimo do pedido para ganhar frete grátis.\n'
            '   Exemplo: R$ 299,90\n'
            '   Se não oferece frete grátis, deixe 0.\n'
            '   Dica: Esta é uma das primeiras perguntas que clientes fazem!\n\n'
            '2. PRAZO DE TROCA (DIAS)\n'
            '   Por lei (CDC), o consumidor tem 7 dias para desistência em compras online.\n'
            '   Muitas lojas oferecem 30 dias. Coloque o prazo da SUA loja.\n'
            '   Exemplo: 30 dias\n\n'
            '3. PRAZO DE DEVOLUÇÃO (DIAS)\n'
            '   Direito de arrependimento (compras online): mínimo 7 dias por lei.\n'
            '   Exemplo: 7 dias\n\n'
            '4. PARCELAMENTO MÁXIMO\n'
            '   Número máximo de parcelas no cartão de crédito.\n'
            '   Exemplo: 12x\n'
            '   Dica: Informe se é COM ou SEM juros (a maioria é sem juros).\n\n'
            '5. PARCELA MÍNIMA (R$)\n'
            '   Valor mínimo de cada parcela.\n'
            '   Exemplo: R$ 50,00\n'
            '   Isso evita que o cliente tente parcelar R$ 100 em 12x.\n\n'
            '6. FORMAS DE PAGAMENTO\n'
            '   Marque todas que sua loja aceita:\n'
            '   • PIX - pagamento instantâneo (geralmente com desconto)\n'
            '   • Cartão de Crédito - parcelamento\n'
            '   • Cartão de Débito - à vista\n'
            '   • Boleto Bancário - compensação em 1-3 dias úteis\n'
            '   • Transferência Bancária\n\n'
            '7. DESCONTO PIX (%)\n'
            '   Percentual de desconto para pagamento via PIX.\n'
            '   Exemplo: 10%\n'
            '   Se não oferece desconto no PIX, coloque 0.\n'
            '   Dica: Desconto PIX é um ótimo argumento de venda!\n\n'
            '8. PRAZO MÉDIO DE ENTREGA (DIAS ÚTEIS)\n'
            '   Tempo médio de entrega para a maioria dos destinos.\n'
            '   Exemplo: 7 dias úteis\n'
            '   Dica: Seja realista. Prometer 3 dias e entregar em 10 gera reclamação.\n\n'
            '9. POLÍTICA DE GARANTIA\n'
            '   Descreva a garantia dos produtos.\n'
            '   Exemplo: "Garantia de 90 dias contra defeitos de fabricação.\n'
            '   Eletrônicos possuem garantia estendida de 1 ano."\n\n'
            'ATENÇÃO: Estas informações devem ser PRECISAS. O agente vai usar exatamente\n'
            'o que você colocar aqui. Informação errada = cliente insatisfeito.'
        ),
        'tempo_estimado': 15,
    },

    # 1.4 Criar Agente(s)
    {
        'ordem': 5,
        'titulo': '1.4 - Criar e configurar o agente',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'A personalidade do agente define como ele vai conversar com seus clientes.\n'
            'Um agente bem configurado parece natural e gera confiança.\n\n'
            'COMO FAZER:\n\n'
            '1. NOME DO AGENTE\n'
            '   Escolha um nome que combine com sua marca.\n'
            '   Exemplos:\n'
            '   • "Ana" - pessoal, amigável (bom para moda, beleza)\n'
            '   • "Atendimento Tarragona" - institucional (bom para B2B)\n'
            '   • "Lucas" - jovem, descontraído (bom para tech, games)\n'
            '   Dica: Nomes femininos tendem a ter melhor aceitação em atendimento.\n\n'
            '2. TIPO DO AGENTE\n'
            '   Escolha o foco principal:\n'
            '   • VENDAS - foco em conversão, upsell, apresentar produtos\n'
            '     Melhor para: lojas que querem aumentar vendas via WhatsApp\n'
            '   • PÓS-VENDA - foco em suporte, trocas, devoluções\n'
            '     Melhor para: lojas com alto volume de suporte\n'
            '   • MARKETING - foco em campanhas, promoções, novidades\n'
            '     Melhor para: lojas que fazem muitas ações promocionais\n'
            '   • TRIAGEM - apenas direciona para o setor correto\n'
            '     Melhor para: empresas com vários departamentos\n'
            '   • GERAL - faz um pouco de tudo (recomendado para começar)\n\n'
            '3. TOM DE VOZ\n'
            '   • FORMAL: "Prezado(a) cliente, como posso auxiliá-lo(a)?"\n'
            '     Melhor para: joalheria, advocacia, medicina, B2B\n'
            '   • INFORMAL: "Oi! Tudo bem? Como posso te ajudar?"\n'
            '     Melhor para: moda jovem, pet, esportes, alimentação\n'
            '   • NEUTRO: "Olá! Como posso ajudar você?"\n'
            '     Melhor para: quando não tem certeza, funciona para tudo\n\n'
            '4. USO DE EMOJIS\n'
            '   • MODERADO: Usa alguns emojis para ser mais expressivo 😊\n'
            '     Recomendado para a maioria dos e-commerces\n'
            '   • BASTANTE: Usa muitos emojis em cada mensagem 🎉🔥✨\n'
            '     Bom para público jovem e marcas descoladas\n'
            '   • NÃO USAR: Sem emojis, 100% texto\n'
            '     Bom para marcas premium e corporativas\n\n'
            '5. CUMPRIMENTO PADRÃO\n'
            '   A primeira mensagem que o agente envia quando um cliente inicia conversa.\n'
            '   Exemplos:\n'
            '   • "Olá! Sou a Ana, assistente virtual da Tarragona. Como posso te ajudar hoje?"\n'
            '   • "Oi! Bem-vindo(a) à [Loja]! Estou aqui para ajudar com produtos,\n'
            '     pedidos ou qualquer dúvida. Como posso te ajudar?"\n'
            '   Dica: Seja breve, simpático e já mostre que pode ajudar.\n\n'
            '6. PERSONA / PERSONALIDADE\n'
            '   ⭐ ESTE É O CAMPO MAIS IMPORTANTE DO TREINAMENTO ⭐\n'
            '   Descreva em detalhes como o agente deve se comportar.\n'
            '   Quanto mais detalhado, melhor o resultado.\n\n'
            '   EXEMPLO COMPLETO:\n'
            '   "Você é a Ana, assistente virtual da Tarragona Store. Seja simpática,\n'
            '   prestativa e paciente. Use linguagem informal mas respeitosa.\n'
            '   NUNCA invente informações sobre produtos - se não souber, diga que vai\n'
            '   verificar. Sempre ofereça alternativas quando um produto não está disponível.\n'
            '   Destaque o frete grátis acima de R$299 e o desconto de 10% no PIX.\n'
            '   Quando o cliente parecer indeciso, pergunte sobre preferências (cor, tamanho)\n'
            '   para ajudar na escolha. Se o cliente estiver irritado, peça desculpas\n'
            '   primeiro e só depois ofereça solução. Nunca discuta com o cliente."\n\n'
            '7. TAMANHO DA MENSAGEM\n'
            '   • CURTO (até 100 caracteres): Respostas rápidas, tipo chat\n'
            '   • MÉDIO (até 300 caracteres): Equilíbrio entre informação e brevidade\n'
            '     Recomendado para WhatsApp\n'
            '   • LONGO (até 500 caracteres): Respostas detalhadas\n'
            '     Melhor para email ou quando precisa explicar muito\n\n'
            '8. SIMULAR DIGITAÇÃO\n'
            '   Se "Sim", o agente espera alguns segundos antes de responder,\n'
            '   simulando que está digitando (como um humano faria).\n'
            '   Recomendado: SIM - faz a conversa parecer mais natural.'
        ),
        'tempo_estimado': 15,
    },

    # 1.5 Escalação
    {
        'ordem': 6,
        'titulo': '1.5 - Configurar regras de escalação para humano',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'O agente não pode (e não deve) resolver TUDO sozinho. Algumas situações\n'
            'precisam de um humano. Configurar isso corretamente evita que clientes\n'
            'fiquem frustrados com um robô que não resolve o problema.\n\n'
            'COMO FAZER:\n\n'
            '1. QUANDO ESCALAR:\n'
            '   Para cada situação, marque Sim ou Não:\n\n'
            '   • CLIENTE PEDE ATENDENTE HUMANO → Recomendado: SIM\n'
            '     Quando o cliente diz "quero falar com alguém", "quero um atendente",\n'
            '     o agente deve transferir IMEDIATAMENTE. Forçar interação com robô\n'
            '     quando o cliente não quer é a receita para perder o cliente.\n\n'
            '   • RECLAMAÇÕES GRAVES → Recomendado: SIM\n'
            '     Exemplos: produto com defeito, pedido extraviado, cobrança indevida.\n'
            '     O agente pode coletar as informações iniciais, mas um humano\n'
            '     deve assumir a resolução.\n\n'
            '   • PEDIDOS DE CANCELAMENTO → Recomendado: SIM\n'
            '     Cancelamentos envolvem reembolso e processos internos.\n'
            '     Um humano tem mais poder de negociação para reter o cliente.\n\n'
            '   • AGENTE NÃO SABE RESPONDER → Recomendado: SIM\n'
            '     Melhor escalar do que inventar uma resposta errada.\n'
            '     O agente avisa: "Vou verificar com a equipe e já retorno."\n\n'
            '   • PEDIDOS DE VALOR ALTO → Defina o valor\n'
            '     Exemplo: Pedidos acima de R$ 500,00\n'
            '     Clientes VIP ou pedidos grandes merecem atenção personalizada.\n'
            '     Coloque 0 se não quiser escalar por valor.\n\n'
            '2. MENSAGEM DE ESCALAÇÃO\n'
            '   O que o agente diz ao cliente quando vai transferir:\n'
            '   Exemplo: "Entendo! Vou transferir você para um de nossos especialistas\n'
            '   que poderá te ajudar melhor com isso. Um momento, por favor!"\n'
            '   Dica: Seja positivo. Não diga "não consigo resolver", diga\n'
            '   "vou te conectar com alguém que pode ajudar ainda melhor".\n\n'
            '3. COMO NOTIFICAR A ESCALAÇÃO\n'
            '   Escolha como o responsável será avisado:\n'
            '   • WhatsApp do responsável - notificação instantânea (recomendado)\n'
            '   • Email - para registrar formalmente\n'
            '   • Notificação no sistema - aparece no painel\n'
            '   • Todos os canais - máxima garantia de que alguém vai ver\n\n'
            '4. CONTATO DO RESPONSÁVEL\n'
            '   WhatsApp ou email de quem vai receber as escalações.\n'
            '   Pode ser o dono, gerente ou líder de atendimento.\n'
            '   Dica: Tenha pelo menos 2 pessoas configuradas para não depender de uma só.\n\n'
            'BOAS PRÁTICAS:\n'
            '• Melhor escalar demais do que de menos no início\n'
            '• Depois que ganhar confiança no agente, reduza as regras de escalação\n'
            '• Revise mensalmente as conversas escaladas para ajustar'
        ),
        'tempo_estimado': 10,
    },

    # ============================================
    # FASE 2: BASE DE CONHECIMENTO
    # ============================================
    {
        'ordem': 7,
        'titulo': '📚 FASE 2: BASE DE CONHECIMENTO',
        'descricao': (
            'Nesta fase você vai alimentar o agente com todo o conhecimento que ele precisa.\n'
            'Pense nisso como o "treinamento de produto" que todo vendedor novo recebe.\n\n'
            'O agente precisa conhecer:\n'
            '• Seus produtos (catálogo completo com preços e disponibilidade)\n'
            '• Suas políticas (FAQ, trocas, garantia)\n'
            '• Seu estilo de atendimento (conversas exemplo)\n\n'
            'O QUE SERÁ FEITO:\n'
            '• Conectar integração de produtos (Bling ou WooCommerce)\n'
            '• Sincronizar catálogo automaticamente\n'
            '• Cadastrar perguntas frequentes e políticas\n'
            '• Importar conversas exemplo de atendimentos reais\n\n'
            'TEMPO ESTIMADO: ~70 minutos\n\n'
            'DICA: Esta é a fase mais importante! Quanto mais conhecimento o agente tiver,\n'
            'menos ele vai errar e menos escalações serão necessárias.'
        ),
        'tempo_estimado': 0,
    },

    # 2.1 Integração de Produtos
    {
        'ordem': 8,
        'titulo': '2.1 - Conectar integração de produtos',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'Sem acesso ao catálogo, o agente não consegue informar preços, disponibilidade\n'
            'ou detalhes dos produtos. A integração automática mantém tudo atualizado.\n\n'
            'COMO FAZER:\n\n'
            'OPÇÃO A: BLING ERP (Recomendado)\n'
            'O Bling é recomendado porque tem melhor pesquisa de produtos e já está\n'
            'integrado ao sistema de pedidos.\n\n'
            '  Passo 1: Acesse o Bling (www.bling.com.br)\n'
            '  Passo 2: Vá em Preferências > Usuários e vendedores\n'
            '  Passo 3: Clique no seu usuário\n'
            '  Passo 4: Vá na aba "API" ou "Integrações"\n'
            '  Passo 5: Clique em "Gerar Token de API"\n'
            '  Passo 6: Copie o token gerado\n'
            '  Passo 7: Cole no campo "Token API" no Neuraxo Agents\n'
            '  Passo 8: Clique em "Testar Conexão"\n'
            '  Passo 9: Se aparecer "Conectado com sucesso", está pronto!\n\n'
            'OPÇÃO B: WOOCOMMERCE\n'
            'Para lojas que usam WordPress + WooCommerce.\n\n'
            '  Passo 1: Acesse o painel WordPress da loja\n'
            '  Passo 2: Vá em WooCommerce > Configurações > Avançado > REST API\n'
            '  Passo 3: Clique em "Adicionar chave"\n'
            '  Passo 4: Descrição: "Neuraxo Agents"\n'
            '  Passo 5: Permissões: "Leitura" (Read)\n'
            '  Passo 6: Clique em "Gerar chave de API"\n'
            '  Passo 7: IMPORTANTE: Copie a Consumer Key (ck_xxx) e Consumer Secret (cs_xxx)\n'
            '           Elas só aparecem UMA VEZ!\n'
            '  Passo 8: Cole as chaves nos campos correspondentes no Neuraxo Agents\n'
            '  Passo 9: Informe a URL da loja (ex: https://www.minhaloja.com.br)\n'
            '  Passo 10: Clique em "Testar Conexão"\n\n'
            'OPÇÃO C: CADASTRO MANUAL\n'
            'Se não usa Bling nem WooCommerce, você pode cadastrar produtos manualmente.\n'
            'Não recomendado para catálogos grandes (acima de 50 produtos).\n\n'
            'PROBLEMAS COMUNS:\n'
            '• "Conexão recusada" → Verifique se o token/chave está correto\n'
            '• "Sem produtos" → Verifique se existem produtos ATIVOS no sistema\n'
            '• "Timeout" → O servidor do Bling/WooCommerce pode estar lento, tente novamente'
        ),
        'tempo_estimado': 15,
    },

    # 2.2 Sincronizar Catálogo
    {
        'ordem': 9,
        'titulo': '2.2 - Sincronizar catálogo de produtos',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'O catálogo precisa estar sempre atualizado. Se um produto esgotou e o agente\n'
            'ainda oferece, o cliente vai ficar frustrado.\n\n'
            'COMO FAZER:\n\n'
            'Passo 1: PRIMEIRA SINCRONIZAÇÃO\n'
            '  Clique em "Sincronizar Catálogo" no painel.\n'
            '  Aguarde a importação (pode levar alguns minutos para catálogos grandes).\n'
            '  O sistema vai importar: nome, descrição, preço, estoque, imagens e categorias.\n\n'
            'Passo 2: REVISAR PRODUTOS\n'
            '  Após a importação, revise os produtos na lista:\n'
            '  • Os nomes estão corretos? (Ex: "CAM-001" não é um bom nome para o cliente)\n'
            '  • Os preços estão atualizados?\n'
            '  • As descrições fazem sentido para um cliente?\n'
            '  • Os produtos inativos/esgotados foram excluídos?\n\n'
            'Passo 3: FREQUÊNCIA DE SINCRONIZAÇÃO\n'
            '  Defina com que frequência o catálogo deve ser atualizado automaticamente:\n\n'
            '  • A CADA 1 HORA → Para lojas com estoque que muda rápido\n'
            '    Ex: eletrônicos, ingressos, produtos limitados\n\n'
            '  • A CADA 6 HORAS → Bom equilíbrio (recomendado para a maioria)\n'
            '    Ex: moda, casa, beleza\n\n'
            '  • A CADA 12 HORAS → Para catálogos estáveis\n'
            '    Ex: produtos sob encomenda, B2B\n\n'
            '  • UMA VEZ POR DIA → Para catálogos que quase não mudam\n\n'
            '  • APENAS MANUAL → Você sincroniza quando quiser\n'
            '    Cuidado: fácil esquecer e o catálogo ficar desatualizado\n\n'
            'DICA: Se você tem promoções relâmpago ou estoque limitado,\n'
            'use sincronização a cada 1 hora para evitar vender produto esgotado.'
        ),
        'tempo_estimado': 10,
    },

    # 2.3 Políticas e FAQ
    {
        'ordem': 10,
        'titulo': '2.3 - Cadastrar políticas e FAQ',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'As perguntas abaixo representam 80% do que os clientes perguntam.\n'
            'Se o agente souber responder tudo isso, vai resolver a maioria dos casos sozinho.\n\n'
            'COMO FAZER:\n'
            'Para cada pergunta abaixo, escreva a resposta que o agente deve dar.\n'
            'Seja específico e use a linguagem da sua empresa.\n\n'
            '══════════════════════════════════\n'
            'CATEGORIA: PRODUTOS\n'
            '══════════════════════════════════\n\n'
            '1. "Como descrever produtos para o cliente?"\n'
            '   Defina o padrão que o agente deve seguir ao apresentar um produto.\n'
            '   Exemplo: "Sempre mencionar: nome do produto, material/composição,\n'
            '   tamanhos disponíveis, cores, preço à vista e parcelado."\n\n'
            '2. "Sugerir produtos similares quando indisponível?"\n'
            '   Sim ou Não. Se sim, o agente vai procurar alternativas no catálogo.\n'
            '   Exemplo: Cliente pede "vestido preto M" que esgotou → agente sugere\n'
            '   "vestido preto G" ou "vestido azul-marinho M".\n\n'
            '3. "O que fazer quando o produto estiver esgotado?"\n'
            '   Exemplo: "Informar que está temporariamente indisponível, sugerir\n'
            '   produtos similares, e oferecer para avisar quando voltar ao estoque.\n'
            '   Coletar email ou WhatsApp para aviso."\n\n'
            '4. "O que fazer quando não tem o tamanho?"\n'
            '   Exemplo: "Verificar se há previsão de reposição. Se não houver,\n'
            '   sugerir o tamanho mais próximo ou modelo similar que tenha o tamanho."\n\n'
            '══════════════════════════════════\n'
            'CATEGORIA: PREÇOS E PAGAMENTO\n'
            '══════════════════════════════════\n\n'
            '5. "Pode dar desconto? Até quanto?"\n'
            '   Exemplo: "Não oferecer desconto por conta própria. Se o cliente pedir,\n'
            '   informar que já temos desconto de 10% no PIX. Para compras acima\n'
            '   de R$500, pode oferecer frete grátis como diferencial."\n'
            '   Ou: "Desconto de até 5% para pagamento à vista, autorizado."\n\n'
            '6. "Como responder quando o cliente diz que está caro?"\n'
            '   Exemplo: "Destacar a qualidade do produto, o custo-benefício,\n'
            '   a possibilidade de parcelamento sem juros, e o desconto no PIX.\n'
            '   Ex: \'Entendo! Esse produto é feito em couro legítimo e tem garantia\n'
            '   de 1 ano. No PIX fica R$XX com 10% de desconto, e no cartão\n'
            '   você pode parcelar em até 12x sem juros!\'."\n\n'
            '7. "Como explicar o parcelamento?"\n'
            '   Exemplo: "Parcelamos em até 12x sem juros no cartão de crédito.\n'
            '   Parcela mínima de R$50. Para um produto de R$600, fica\n'
            '   12x de R$50 sem juros."\n\n'
            '══════════════════════════════════\n'
            'CATEGORIA: FRETE E ENTREGA\n'
            '══════════════════════════════════\n\n'
            '8. "Como calcular/informar frete?"\n'
            '   Exemplo: "Pedir o CEP do cliente e consultar na tabela.\n'
            '   Informar valor e prazo. Lembrar do frete grátis acima de R$299.\n'
            '   Ex: \'Me passa seu CEP que eu calculo o frete pra você! Lembrando\n'
            '   que acima de R$299 o frete é grátis 😉\'."\n\n'
            '9. "Quais transportadoras utiliza?"\n'
            '   Exemplo: "Correios (PAC e SEDEX), Jadlog e Total Express.\n'
            '   Prazo varia conforme a região."\n\n'
            '10. "O que fazer em caso de atraso na entrega?"\n'
            '    Exemplo: "Pedir o número do pedido, verificar o rastreamento,\n'
            '    informar a situação ao cliente. Se estiver realmente atrasado,\n'
            '    pedir desculpas e abrir chamado com a transportadora.\n'
            '    Se o atraso for maior que 5 dias úteis, escalar para humano."\n\n'
            '══════════════════════════════════\n'
            'CATEGORIA: TROCAS E DEVOLUÇÕES\n'
            '══════════════════════════════════\n\n'
            '11. "Como iniciar processo de troca?"\n'
            '    Exemplo: "Solicitar: número do pedido, motivo da troca,\n'
            '    fotos do produto (se defeito). Informar o prazo de troca (30 dias).\n'
            '    Enviar link/instruções de como postar a devolução."\n\n'
            '12. "Cliente paga frete da troca?"\n'
            '    Escolha:\n'
            '    • LOJA PAGA → Em todos os casos\n'
            '    • CLIENTE PAGA → Em todos os casos\n'
            '    • DEPENDE DO MOTIVO → Defeito = loja paga / Arrependimento = cliente paga\n'
            '    Dica: Pela lei, em desistência (7 dias) o frete é da loja.\n\n'
            '══════════════════════════════════\n'
            'CATEGORIA: RECLAMAÇÕES\n'
            '══════════════════════════════════\n\n'
            '13. "Como lidar com cliente irritado?"\n'
            '    Exemplo: "PRIMEIRO: pedir desculpas genuinamente.\n'
            '    SEGUNDO: demonstrar empatia (\'Entendo sua frustração\').\n'
            '    TERCEIRO: buscar solução rápida.\n'
            '    NUNCA: discutir, minimizar o problema, ou culpar o cliente.\n'
            '    Se o cliente xingar ou ameaçar, escalar para humano."\n\n'
            '14. "Pode oferecer compensação?"\n'
            '    Exemplo: "Sim, em caso de falha nossa:\n'
            '    • Cupom de 10% na próxima compra\n'
            '    • Frete grátis no próximo pedido\n'
            '    • Brinde surpresa junto com a resolução\n'
            '    Para compensações maiores (reembolso parcial), escalar para gerente."\n\n'
            '15. "Quando escalar para gerente?"\n'
            '    Exemplo: "Escalar quando:\n'
            '    • Cliente ameaça processo ou Procon\n'
            '    • Pedido de reembolso acima de R$200\n'
            '    • Reclamação em redes sociais\n'
            '    • Erro repetido (cliente com problema pela 2ª+ vez)\n'
            '    • Cliente VIP (já comprou mais de 5 vezes)"'
        ),
        'tempo_estimado': 30,
    },

    # 2.4 Conversas Exemplo
    {
        'ordem': 11,
        'titulo': '2.4 - Importar conversas exemplo',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'Conversas reais são o MELHOR material de treinamento. O agente aprende o tom,\n'
            'as expressões, o ritmo e o estilo de atendimento da sua empresa.\n'
            'É como colocar um funcionário novo para "ouvir" os atendimentos dos veteranos.\n\n'
            'COMO FAZER:\n\n'
            'MÉTODO 1: EXPORTAR DO WHATSAPP (Recomendado)\n\n'
            '  No celular:\n'
            '  Passo 1: Abra o WhatsApp e encontre uma conversa de atendimento BEM FEITO\n'
            '  Passo 2: Toque no nome do contato (topo da tela)\n'
            '  Passo 3: Role para baixo e toque em "Exportar conversa"\n'
            '  Passo 4: Escolha "Sem mídia" (não precisa das fotos/vídeos)\n'
            '  Passo 5: Envie o arquivo .txt por email ou salve no Google Drive\n'
            '  Passo 6: Faça upload do arquivo no Neuraxo Agents\n\n'
            '  Repita para 5-10 conversas de bom atendimento.\n\n'
            'MÉTODO 2: CADASTRAR MANUALMENTE\n\n'
            '  Se não tem backup do WhatsApp, crie conversas exemplo:\n'
            '  Passo 1: Pense em perguntas que os clientes fazem TODO DIA\n'
            '  Passo 2: Escreva a PERGUNTA do cliente e a RESPOSTA IDEAL\n\n'
            '  Exemplos:\n\n'
            '  PERGUNTA: "Boa tarde, vocês têm frete grátis?"\n'
            '  RESPOSTA: "Boa tarde! Sim, temos frete grátis para compras acima\n'
            '  de R$299! Abaixo desse valor, o frete é calculado pelo CEP.\n'
            '  Quer me passar seu CEP para eu calcular?"\n\n'
            '  PERGUNTA: "Esse vestido tem no tamanho P?"\n'
            '  RESPOSTA: "Deixa eu verificar! [consulta catálogo] Temos sim!\n'
            '  O vestido X está disponível nos tamanhos P, M e G.\n'
            '  O P veste de 34 a 36. Quer que eu envie mais detalhes?"\n\n'
            '  PERGUNTA: "Meu pedido não chegou, já faz 10 dias"\n'
            '  RESPOSTA: "Puxa, me desculpa pelo transtorno! Me passa o número\n'
            '  do seu pedido que eu verifico o rastreamento pra você agora mesmo."\n\n'
            'QUAIS CONVERSAS PRIORIZAR:\n'
            '• ✅ Atendimentos que resultaram em venda\n'
            '• ✅ Resolução de problemas com cliente satisfeito\n'
            '• ✅ Situações comuns do dia a dia\n'
            '• ✅ Conversas que mostram o tom de voz ideal\n'
            '• ❌ Evitar conversas com informações pessoais dos clientes\n'
            '• ❌ Evitar conversas onde o atendente errou\n'
            '• ❌ Evitar conversas muito longas e confusas\n\n'
            'QUANTIDADE RECOMENDADA:\n'
            '• Mínimo: 5 conversas\n'
            '• Ideal: 15-30 conversas\n'
            '• Ótimo: 50+ conversas\n'
            'Quanto mais, melhor o agente aprende!'
        ),
        'tempo_estimado': 20,
    },

    # ============================================
    # FASE 3: TREINAMENTO INTERATIVO
    # ============================================
    {
        'ordem': 12,
        'titulo': '🎯 FASE 3: TREINAMENTO INTERATIVO',
        'descricao': (
            'Nesta fase você vai TESTAR o agente como se fosse um cliente.\n'
            'É como um "test drive" antes de colocar na rua.\n\n'
            'O objetivo é encontrar falhas, corrigir e melhorar até que o agente\n'
            'responda corretamente na maioria dos cenários.\n\n'
            'O QUE SERÁ FEITO:\n'
            '• Chat de teste interno (você conversa com o agente)\n'
            '• Avaliação das respostas (nota 1-5 para cada resposta)\n'
            '• Correção das respostas ruins\n'
            '• Novos testes para validar as melhorias\n\n'
            'TEMPO ESTIMADO: ~70 minutos\n\n'
            'DICA: Chame colegas para testar também! Cada pessoa vai pensar em\n'
            'perguntas diferentes e encontrar falhas que você não encontraria sozinho.'
        ),
        'tempo_estimado': 0,
    },

    # 3.1 Chat de Teste
    {
        'ordem': 13,
        'titulo': '3.1 - Realizar chat de teste interno',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'Você não colocaria um funcionário novo para atender sem antes testar, certo?\n'
            'O mesmo vale para o agente. Teste ANTES de colocar com clientes reais.\n\n'
            'COMO FAZER:\n'
            'Acesse o "Chat de Teste" no painel e simule ser um cliente.\n'
            'Teste TODOS os cenários abaixo, um por um:\n\n'
            '══════════════════════════════════\n'
            'CENÁRIO 1: CONSULTANDO PRODUTO\n'
            '══════════════════════════════════\n'
            'Envie: "Oi, vocês têm camiseta branca tamanho M?"\n'
            'O agente deve:\n'
            '• Cumprimentar\n'
            '• Buscar no catálogo\n'
            '• Informar disponibilidade, preço e detalhes\n'
            '• Oferecer para enviar foto/link\n\n'
            '══════════════════════════════════\n'
            'CENÁRIO 2: PREÇO E PARCELAMENTO\n'
            '══════════════════════════════════\n'
            'Envie: "Quanto custa o tênis X? Parcela em quantas vezes?"\n'
            'O agente deve:\n'
            '• Informar preço à vista (com desconto PIX se houver)\n'
            '• Informar opções de parcelamento\n'
            '• Não inventar preço de produto que não existe\n\n'
            '══════════════════════════════════\n'
            'CENÁRIO 3: FRETE\n'
            '══════════════════════════════════\n'
            'Envie: "Qual o valor do frete para o CEP 01310-100?"\n'
            'O agente deve:\n'
            '• Calcular ou informar como calcular\n'
            '• Mencionar frete grátis se o pedido se qualificar\n'
            '• Informar prazo estimado\n\n'
            '══════════════════════════════════\n'
            'CENÁRIO 4: TROCA DE PRODUTO\n'
            '══════════════════════════════════\n'
            'Envie: "Comprei uma camisa e veio com defeito, quero trocar"\n'
            'O agente deve:\n'
            '• Pedir desculpas\n'
            '• Pedir número do pedido e fotos\n'
            '• Explicar o processo de troca\n'
            '• Informar quem paga o frete\n\n'
            '══════════════════════════════════\n'
            'CENÁRIO 5: CLIENTE IRRITADO\n'
            '══════════════════════════════════\n'
            'Envie: "Já faz 15 dias e meu pedido não chegou! Quero meu dinheiro de volta!"\n'
            'O agente deve:\n'
            '• Pedir desculpas PRIMEIRO\n'
            '• Demonstrar empatia\n'
            '• Pedir número do pedido\n'
            '• Verificar rastreamento\n'
            '• NÃO discutir\n\n'
            '══════════════════════════════════\n'
            'CENÁRIO 6: PEDIR HUMANO\n'
            '══════════════════════════════════\n'
            'Envie: "Quero falar com uma pessoa de verdade, não com robô"\n'
            'O agente deve:\n'
            '• Respeitar o pedido\n'
            '• Transferir para humano com mensagem positiva\n'
            '• NÃO insistir em continuar a conversa\n\n'
            '══════════════════════════════════\n'
            'CENÁRIO 7: FORA DO ESCOPO\n'
            '══════════════════════════════════\n'
            'Envie: "Qual a capital da França?" ou "Me conta uma piada"\n'
            'O agente deve:\n'
            '• Redirecionar educadamente para o assunto da loja\n'
            '• NÃO responder perguntas que não são do negócio\n'
            '• Exemplo: "Haha, boa pergunta! Mas como sou assistente da [Loja],\n'
            '  posso te ajudar com nossos produtos e pedidos. Posso ajudar em algo?"\n\n'
            'DICA: Anote as respostas que ficaram ruins para corrigir na próxima etapa.'
        ),
        'tempo_estimado': 30,
    },

    # 3.2 Avaliação
    {
        'ordem': 14,
        'titulo': '3.2 - Avaliar respostas do agente',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'Avaliar as respostas é como dar feedback a um funcionário.\n'
            'O agente aprende com suas correções e melhora a cada ciclo.\n\n'
            'COMO FAZER:\n\n'
            'Passo 1: REVISAR CADA RESPOSTA DO CHAT DE TESTE\n'
            '  Para cada resposta, dê uma nota de 1 a 5:\n'
            '  ⭐⭐⭐⭐⭐ (5) = PERFEITO - Resposta exatamente como deveria ser\n'
            '  ⭐⭐⭐⭐ (4) = BOM - Pequenos ajustes mas no geral correto\n'
            '  ⭐⭐⭐ (3) = ACEITÁVEL - Funciona mas poderia melhorar bastante\n'
            '  ⭐⭐ (2) = RUIM - Informação incompleta ou tom errado\n'
            '  ⭐ (1) = ERRADO - Informação incorreta ou resposta inadequada\n\n'
            'Passo 2: CORRIGIR RESPOSTAS COM NOTA ABAIXO DE 3\n'
            '  Para cada resposta ruim, escreva a RESPOSTA CORRETA.\n'
            '  O sistema vai usar essa correção para retreinar o agente.\n\n'
            '  Exemplo de correção:\n'
            '  Resposta do agente: "O frete é R$15"\n'
            '  Problema: Inventou o valor sem consultar\n'
            '  Resposta correta: "Me passa seu CEP que eu calculo o frete certinho\n'
            '  pra você! Lembrando que acima de R$299 o frete é grátis."\n\n'
            'Passo 3: VERIFICAR PONTOS CRÍTICOS\n'
            '  Responda a estas perguntas:\n\n'
            '  ❓ O agente INVENTOU informações?\n'
            '     CRÍTICO! Se inventou preço, prazo ou característica de produto,\n'
            '     precisa corrigir urgentemente. Informação falsa para cliente real\n'
            '     pode gerar processo, reclamação no Procon ou perda do cliente.\n\n'
            '  ❓ O TOM DE VOZ está adequado?\n'
            '     Se configurou "informal" e o agente está usando "prezado(a)",\n'
            '     precisa ajustar. O tom deve ser consistente.\n\n'
            '  ❓ O agente ESCALOU quando deveria?\n'
            '     No cenário do cliente irritado e do pedido de humano,\n'
            '     o agente transferiu corretamente? Se não, ajustar as regras.\n\n'
            'DICA: Não se preocupe se muitas respostas ficarem ruins no início.\n'
            'É normal! O treinamento é iterativo - cada correção melhora o agente.'
        ),
        'tempo_estimado': 20,
    },

    # 3.3 Refinamento
    {
        'ordem': 15,
        'titulo': '3.3 - Refinar e fazer novos testes',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'Treinamento é um ciclo: Testar → Avaliar → Corrigir → Testar de novo.\n'
            'Cada ciclo melhora o agente. O objetivo é alcançar 80%+ de acerto.\n\n'
            'COMO FAZER:\n\n'
            'Passo 1: GERAR EXEMPLOS AUTOMÁTICOS\n'
            '  Após suas correções, clique em "Gerar Exemplos".\n'
            '  O sistema cria variações das correções para reforçar o aprendizado.\n'
            '  Ex: Se você corrigiu "como informar frete", o sistema cria variações:\n'
            '  • "Quanto é a entrega?"\n'
            '  • "Tem frete grátis?"\n'
            '  • "Qual o prazo de entrega?"\n'
            '  Todas com a resposta correta baseada na sua correção.\n\n'
            'Passo 2: NOVO CHAT DE TESTE\n'
            '  Repita os cenários que deram problema.\n'
            '  Verifique se o agente melhorou.\n'
            '  Compare o score antes e depois.\n\n'
            'Passo 3: REPETIR ATÉ SATISFEITO\n'
            '  Ciclo recomendado:\n'
            '  • 1ª rodada: Espere ~60-70% de acerto (normal para início)\n'
            '  • 2ª rodada: Após correções, deve subir para ~75-85%\n'
            '  • 3ª rodada: Ajustes finos, deve atingir ~85-95%\n\n'
            '  Se após 3 rodadas o score ainda estiver abaixo de 80%:\n'
            '  • Revise se o FAQ (etapa 2.3) está completo\n'
            '  • Adicione mais conversas exemplo (etapa 2.4)\n'
            '  • Revise a persona do agente (etapa 1.4)\n\n'
            'QUANDO AVANÇAR PARA A PRÓXIMA FASE?\n'
            '• Score geral acima de 80%\n'
            '• Nenhuma resposta com informação inventada\n'
            '• Tom de voz consistente\n'
            '• Escalação funcionando corretamente\n\n'
            'DICA: Se possível, peça para outra pessoa testar o agente.\n'
            'Olhos frescos encontram problemas que você já se acostumou.'
        ),
        'tempo_estimado': 20,
    },

    # ============================================
    # FASE 4: MÉTRICAS E REFINAMENTO
    # ============================================
    {
        'ordem': 16,
        'titulo': '📊 FASE 4: MÉTRICAS E REFINAMENTO',
        'descricao': (
            'Nesta fase você vai analisar a performance do agente com dados e números,\n'
            'rodar testes automatizados e fazer os ajustes finais.\n\n'
            'Pense nisso como a "prova final" antes da formatura do agente.\n\n'
            'O QUE SERÁ FEITO:\n'
            '• Revisar dashboard de performance com métricas detalhadas\n'
            '• Executar bateria de testes automatizados\n'
            '• Fazer os últimos ajustes\n\n'
            'TEMPO ESTIMADO: ~40 minutos\n\n'
            'REQUISITO: Score acima de 80% nos testes da Fase 3.'
        ),
        'tempo_estimado': 0,
    },

    # 4.1 Dashboard
    {
        'ordem': 17,
        'titulo': '4.1 - Revisar dashboard de performance',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'O dashboard mostra visualmente onde o agente vai bem e onde precisa melhorar.\n'
            'Olhar os números ajuda a tomar decisões baseadas em dados, não em intuição.\n\n'
            'COMO FAZER:\n'
            'Acesse Dashboard > Performance do Agente e analise cada métrica:\n\n'
            '1. SCORE GERAL\n'
            '   Porcentagem de respostas avaliadas como corretas (nota ≥ 3).\n'
            '   • Acima de 90% = Excelente, pronto para go-live\n'
            '   • 80-90% = Bom, pode ir para go-live com monitoramento\n'
            '   • 70-80% = Regular, precisa de mais treinamento\n'
            '   • Abaixo de 70% = Voltar para Fase 3 e fazer mais correções\n\n'
            '2. TAXA DE ACERTO POR CATEGORIA\n'
            '   Score individual para cada assunto:\n'
            '   • Produtos - sabe informar sobre o catálogo?\n'
            '   • Preços - informa corretamente sem inventar?\n'
            '   • Frete - calcula e informa prazo?\n'
            '   • Trocas - conhece a política?\n'
            '   • Reclamações - lida com empatia?\n'
            '   Se alguma categoria está abaixo de 70%, volte ao FAQ (etapa 2.3)\n'
            '   e adicione mais informações sobre esse assunto.\n\n'
            '3. PERGUNTAS MAIS FREQUENTES\n'
            '   Top 10 perguntas que mais apareceram nos testes.\n'
            '   Verifique se o agente responde bem todas elas.\n'
            '   Se alguma pergunta frequente não tem boa resposta, adicione ao FAQ.\n\n'
            '4. CONVERSAS QUE PRECISARAM DE ESCALAÇÃO\n'
            '   Quantas vezes o agente precisou transferir para humano.\n'
            '   • Abaixo de 20% = Ótimo, agente resolve a maioria\n'
            '   • 20-40% = Normal para início\n'
            '   • Acima de 40% = Agente precisa de mais treinamento\n\n'
            '5. TEMPO MÉDIO DE RESPOSTA\n'
            '   Quanto tempo o agente leva para responder.\n'
            '   Ideal: 2-5 segundos (com simulação de digitação pode chegar a 8-10s).'
        ),
        'tempo_estimado': 10,
    },

    # 4.2 Testes Automatizados
    {
        'ordem': 18,
        'titulo': '4.2 - Executar bateria de testes automatizados',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'Testes automatizados verificam centenas de cenários que seria impossível\n'
            'testar manualmente. É como uma "prova" com gabarito.\n\n'
            'COMO FAZER:\n'
            'Clique em "Executar Testes" no painel. O sistema vai rodar 5 baterias:\n\n'
            '✅ TESTE 1: PRODUTOS\n'
            '   O que testa:\n'
            '   • Agente encontra produtos no catálogo?\n'
            '   • Preços informados estão corretos?\n'
            '   • Disponibilidade de estoque está atualizada?\n'
            '   • Descrições dos produtos estão adequadas?\n'
            '   Resultado esperado: ≥ 80% de acerto\n\n'
            '✅ TESTE 2: ATENDIMENTO\n'
            '   O que testa:\n'
            '   • Tom de voz está consistente?\n'
            '   • Cumprimento e despedida adequados?\n'
            '   • Demonstra empatia em situações difíceis?\n'
            '   • Usa emojis conforme configurado?\n'
            '   Resultado esperado: ≥ 85% de acerto\n\n'
            '✅ TESTE 3: POLÍTICAS\n'
            '   O que testa:\n'
            '   • Conhece prazo de troca e devolução?\n'
            '   • Sabe as formas de pagamento?\n'
            '   • Informa frete grátis corretamente?\n'
            '   • Conhece a política de garantia?\n'
            '   Resultado esperado: ≥ 90% de acerto\n\n'
            '✅ TESTE 4: ESCALAÇÃO\n'
            '   O que testa:\n'
            '   • Escala quando cliente pede humano?\n'
            '   • Escala em reclamações graves?\n'
            '   • Escala para pedidos de valor alto?\n'
            '   • Mensagem de escalação está correta?\n'
            '   Resultado esperado: ≥ 95% de acerto (crítico!)\n\n'
            '✅ TESTE 5: SEGURANÇA\n'
            '   O que testa:\n'
            '   • Agente NÃO inventa informações?\n'
            '   • Agente NÃO revela dados sensíveis?\n'
            '   • Agente NÃO sai do escopo da loja?\n'
            '   • Agente NÃO executa ações perigosas?\n'
            '   Resultado esperado: 100% de acerto (obrigatório!)\n\n'
            'APÓS OS TESTES:\n'
            '• Se todos passaram: Parabéns! Avance para os ajustes finais.\n'
            '• Se algum falhou: Revise os cenários que falharam, corrija no FAQ\n'
            '  ou nas conversas exemplo, e rode os testes novamente.'
        ),
        'tempo_estimado': 15,
    },

    # 4.3 Ajustes Finais
    {
        'ordem': 19,
        'titulo': '4.3 - Fazer ajustes finais',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'Estes são os últimos ajustes antes de colocar o agente para atender de verdade.\n'
            'É a hora de calibrar os detalhes finos.\n\n'
            'COMO FAZER:\n\n'
            '1. REVISAR CATEGORIAS COM SCORE BAIXO\n'
            '   Se alguma categoria ficou abaixo de 70% nos testes:\n'
            '   • Volte ao FAQ (etapa 2.3) e adicione mais respostas para essa categoria\n'
            '   • Adicione conversas exemplo sobre esse assunto (etapa 2.4)\n'
            '   • Rode os testes novamente e verifique se melhorou\n\n'
            '2. COBRIR PERGUNTAS SEM RESPOSTA\n'
            '   Os testes podem ter revelado perguntas que o agente não soube responder.\n'
            '   Para cada uma, adicione a resposta ideal no FAQ.\n'
            '   Exemplos comuns que passam batido:\n'
            '   • "Vocês têm loja física?"\n'
            '   • "Aceita vale-presente?"\n'
            '   • "Fazem atacado?"\n'
            '   • "Têm programa de fidelidade?"\n\n'
            '3. AJUSTAR TEMPERATURA DO LLM\n'
            '   A temperatura controla o quão "criativo" o agente é nas respostas.\n\n'
            '   • 0.3 = MUITO CONSERVADOR\n'
            '     Respostas sempre iguais e previsíveis.\n'
            '     Bom para: informações técnicas, dados financeiros\n\n'
            '   • 0.5 = CONSERVADOR (Recomendado para atendimento)\n'
            '     Respostas consistentes com pequenas variações.\n'
            '     Bom para: atendimento ao cliente, FAQ\n\n'
            '   • 0.7 = EQUILIBRADO (Padrão)\n'
            '     Respostas variadas mas ainda coerentes.\n'
            '     Bom para: vendas, marketing\n\n'
            '   • 0.9 = CRIATIVO\n'
            '     Respostas muito variadas, pode surpreender.\n'
            '     Cuidado: pode gerar respostas inconsistentes\n\n'
            '   RECOMENDAÇÃO: Comece com 0.5 e ajuste conforme necessidade.\n\n'
            '4. CHECKLIST FINAL\n'
            '   ☐ Score geral acima de 80%?\n'
            '   ☐ Nenhuma resposta inventando informações?\n'
            '   ☐ Tom de voz consistente?\n'
            '   ☐ Escalação funcionando?\n'
            '   ☐ Teste de segurança 100%?\n\n'
            '   Se todos os itens estão OK, avance para a Fase 5: GO LIVE!'
        ),
        'tempo_estimado': 15,
    },

    # ============================================
    # FASE 5: GO LIVE
    # ============================================
    {
        'ordem': 20,
        'titulo': '🚀 FASE 5: GO LIVE',
        'descricao': (
            'Chegou a hora! Nesta fase você vai conectar o agente ao WhatsApp real,\n'
            'configurar os limites de operação e monitorar as primeiras conversas.\n\n'
            'O QUE SERÁ FEITO:\n'
            '• Conectar a integração com WhatsApp (W-API)\n'
            '• Definir horários e limites de atuação\n'
            '• Executar checklist de pré-lançamento\n'
            '• Ativar o agente e monitorar as primeiras conversas reais\n\n'
            'TEMPO ESTIMADO: ~95 minutos (incluindo monitoramento)\n\n'
            'REQUISITO: Score acima de 80% na Fase 4.\n\n'
            'RECOMENDAÇÃO: Faça o go-live em um dia CALMO (terça ou quarta),\n'
            'de manhã, quando você tem o dia inteiro para monitorar.\n'
            'Evite sexta-feira ou véspera de feriado.'
        ),
        'tempo_estimado': 0,
    },

    # 5.1 WhatsApp
    {
        'ordem': 21,
        'titulo': '5.1 - Conectar WhatsApp (W-API)',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'A W-API é a ponte entre o Neuraxo Agents e o WhatsApp.\n'
            'Sem ela, o agente não consegue enviar nem receber mensagens.\n\n'
            'COMO FAZER:\n\n'
            'PASSO 1: ACESSAR O PAINEL W-API\n'
            '  Acesse o painel da W-API (URL fornecida pelo suporte Neuraxo).\n'
            '  Você vai precisar de 3 informações:\n'
            '  • URL da instância (ex: https://api.w-api.app)\n'
            '  • Token de autenticação\n'
            '  • ID da instância\n\n'
            'PASSO 2: CONFIGURAR NO NEURAXO AGENTS\n'
            '  No painel do Neuraxo Agents, vá em Configurações > WhatsApp:\n'
            '  • Cole a URL da instância\n'
            '  • Cole o Token de autenticação\n'
            '  • Cole o ID da instância\n\n'
            'PASSO 3: TESTAR CONEXÃO\n'
            '  Clique em "Testar Conexão".\n'
            '  Resultados possíveis:\n'
            '  • ✅ "Conectado" → WhatsApp ativo e pronto\n'
            '  • ⚠️ "Desconectado" → Abra o app WhatsApp e escaneie o QR Code\n'
            '  • ❌ "Erro" → Verifique se token e URL estão corretos\n\n'
            'PASSO 4: ENVIAR MENSAGEM DE TESTE\n'
            '  Envie uma mensagem de teste para o seu próprio WhatsApp.\n'
            '  Se recebeu a mensagem, está tudo funcionando!\n\n'
            'PROBLEMAS COMUNS:\n'
            '• "WhatsApp desconectado" → Escaneie o QR Code novamente\n'
            '• "Token inválido" → Gere um novo token no painel W-API\n'
            '• "Mensagem não enviada" → Verifique se o número tem WhatsApp\n'
            '• "Bloqueado pelo WhatsApp" → Pode estar enviando muitas mensagens.\n'
            '  Reduza o volume e espere 24h.\n\n'
            'IMPORTANTE:\n'
            '• Use um número de WhatsApp BUSINESS (não pessoal)\n'
            '• O número deve estar logado e ativo\n'
            '• Mantenha o celular com internet estável'
        ),
        'tempo_estimado': 15,
    },

    # 5.2 Horários e Limites
    {
        'ordem': 22,
        'titulo': '5.2 - Definir horários e limites de atuação',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'Limites protegem contra envio excessivo de mensagens (que pode\n'
            'bloquear o WhatsApp) e garantem comportamento humano e natural.\n\n'
            'COMO FAZER:\n\n'
            '1. ATIVAR ATENDIMENTO AUTOMÁTICO\n'
            '   Marque "Sim" para o agente responder automaticamente.\n'
            '   Se marcar "Não", o agente apenas sugere respostas e um humano envia.\n\n'
            '2. LIMITE DIÁRIO DE MENSAGENS\n'
            '   Quantas mensagens o agente pode enviar por dia.\n'
            '   • Para começar: 100 mensagens/dia\n'
            '   • Depois de estabilizar: 200-300 mensagens/dia\n'
            '   • Máximo recomendado: 500/dia (acima disso risco de bloqueio)\n'
            '   Dica: O WhatsApp pode bloquear contas que enviam muitas mensagens.\n'
            '   Comece baixo e vá aumentando gradualmente.\n\n'
            '3. DELAY ENTRE RESPOSTAS\n'
            '   Tempo que o agente espera antes de responder:\n'
            '   • Delay mínimo: 3 segundos (recomendado)\n'
            '   • Delay máximo: 10 segundos (recomendado)\n'
            '   O agente vai esperar um tempo aleatório entre o mínimo e máximo.\n'
            '   Isso faz parecer que alguém está lendo e digitando.\n'
            '   Delay muito curto (1s) parece robô. Delay muito longo (30s) irrita o cliente.\n\n'
            '4. MODO DE LANÇAMENTO\n'
            '   ⭐ ESCOLHA COM CUIDADO ⭐\n\n'
            '   • SHADOW MODE (Recomendado para o início)\n'
            '     O agente recebe a mensagem, prepara a resposta,\n'
            '     mas NÃO envia. Um humano vê a sugestão e decide enviar ou editar.\n'
            '     Vantagem: Zero risco. Você controla tudo.\n'
            '     Desvantagem: Precisa de alguém monitorando em tempo real.\n'
            '     Use por: 1-2 semanas até ganhar confiança.\n\n'
            '   • SEMI-AUTOMÁTICO\n'
            '     O agente envia as respostas automaticamente,\n'
            '     mas um humano monitora e pode intervir a qualquer momento.\n'
            '     Vantagem: Resposta rápida + supervisão.\n'
            '     Desvantagem: Se o agente errar, o cliente já viu.\n'
            '     Use por: 2-4 semanas após shadow mode.\n\n'
            '   • TOTALMENTE AUTOMÁTICO\n'
            '     O agente trabalha sozinho. Humano só é chamado em escalações.\n'
            '     Vantagem: Escala infinita, sem custo de pessoal.\n'
            '     Desvantagem: Se errar, ninguém corrige em tempo real.\n'
            '     Use após: 1+ mês de semi-automático sem problemas.'
        ),
        'tempo_estimado': 10,
    },

    # 5.3 Checklist Pré-Launch
    {
        'ordem': 23,
        'titulo': '5.3 - Checklist pré-launch',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'Último check antes de ligar o agente. Não pule esta etapa!\n'
            'Um item esquecido pode causar problemas nas primeiras conversas.\n\n'
            'COMO FAZER:\n'
            'Verifique CADA item abaixo e marque como concluído:\n\n'
            '☐ 1. SCORE GERAL ACIMA DE 80%\n'
            '   Verifique no dashboard. Se não está, volte para a Fase 3.\n\n'
            '☐ 2. TODOS OS CENÁRIOS CRÍTICOS TESTADOS\n'
            '   Confirme que testou: consulta de produto, preço, frete,\n'
            '   troca, reclamação, escalação e pergunta fora do escopo.\n\n'
            '☐ 3. ESCALAÇÃO CONFIGURADA E TESTADA\n'
            '   Teste de verdade: peça para falar com humano e veja se\n'
            '   o responsável recebe a notificação.\n\n'
            '☐ 4. WHATSAPP CONECTADO E FUNCIONANDO\n'
            '   Envie uma mensagem de teste e confirme o recebimento.\n\n'
            '☐ 5. HORÁRIOS DE ATENDIMENTO CONFIGURADOS\n'
            '   Verifique: o agente sabe que não atende às 3h da manhã?\n\n'
            '☐ 6. RESPONSÁVEL POR ESCALAÇÕES DEFINIDO\n'
            '   Alguém vai receber e responder as escalações? Quem?\n'
            '   Essa pessoa sabe que vai receber? Foi avisada?\n\n'
            '☐ 7. MENSAGEM DE AUSÊNCIA CONFIGURADA\n'
            '   Teste: mande mensagem fora do horário e veja a resposta.\n\n'
            '☐ 8. BACKUP DE CONVERSAS ATIVADO\n'
            '   Todas as conversas devem ser salvas para análise posterior.\n'
            '   Isso é essencial para continuar melhorando o agente.\n\n'
            'TUDO OK? Então avance para a última etapa e LIGUE O AGENTE!'
        ),
        'tempo_estimado': 10,
    },

    # 5.4 Monitoramento
    {
        'ordem': 24,
        'titulo': '5.4 - Monitorar primeiras conversas reais',
        'descricao': (
            'POR QUE ISSO É IMPORTANTE?\n'
            'Clientes reais são imprevisíveis. Eles vão fazer perguntas que você\n'
            'nunca pensou, usar gírias, mandar áudio, abreviar palavras.\n'
            'Monitorar as primeiras conversas é ESSENCIAL.\n\n'
            'COMO FAZER:\n\n'
            'PASSO 1: ATIVAR O AGENTE\n'
            '  Clique em "Ativar Agente" no painel.\n'
            '  A partir de agora, mensagens reais serão processadas.\n'
            '  Respire fundo. Vai dar certo! 💪\n\n'
            'PASSO 2: MONITORAR AS PRIMEIRAS 10 CONVERSAS\n'
            '  Acompanhe em tempo real no painel "Conversas Ativas".\n'
            '  Para cada conversa, observe:\n'
            '  • O agente entendeu a pergunta corretamente?\n'
            '  • A resposta foi adequada?\n'
            '  • O tom está natural?\n'
            '  • O cliente ficou satisfeito?\n\n'
            '  Se algo der errado:\n'
            '  • No Shadow Mode: simplesmente edite a resposta antes de enviar\n'
            '  • No Semi-Auto: envie uma mensagem manual corrigindo\n'
            '  • Exemplo: "Desculpe, me expressei mal. O que eu quis dizer foi..."\n\n'
            'PASSO 3: AVALIAR QUALIDADE DAS PRIMEIRAS RESPOSTAS\n'
            '  Dê nota para as respostas reais, como fez nos testes.\n'
            '  Compare o score com os testes - geralmente cai um pouco\n'
            '  com clientes reais (normal, eles são mais imprevisíveis).\n\n'
            'PASSO 4: ANOTAR AJUSTES NECESSÁRIOS\n'
            '  Anote tudo que precisa melhorar:\n'
            '  • Perguntas novas que o agente não soube responder\n'
            '  • Gírias/abreviações que confundiram (ex: "qto", "mto", "blz")\n'
            '  • Cenários que não foram cobertos no treinamento\n'
            '  • Produtos ou informações desatualizados\n\n'
            'PASSO 5: APLICAR CORREÇÕES\n'
            '  Volte ao FAQ ou conversas exemplo e adicione as correções.\n'
            '  Rode os testes novamente se necessário.\n\n'
            '══════════════════════════════════\n'
            '🎉 PARABÉNS! TREINAMENTO CONCLUÍDO!\n'
            '══════════════════════════════════\n\n'
            'Seu agente está no ar atendendo clientes reais!\n\n'
            'PRÓXIMOS PASSOS (pós-lançamento):\n'
            '• Revise as conversas diariamente na primeira semana\n'
            '• Revise semanalmente a partir da segunda semana\n'
            '• Adicione novas perguntas ao FAQ conforme surgem\n'
            '• Monitore a taxa de escalação (deve diminuir com o tempo)\n'
            '• A cada mês, rode os testes automatizados novamente\n'
            '• Peça feedback da equipe e dos clientes\n\n'
            'LEMBRE-SE:\n'
            'O treinamento é CONTÍNUO. O agente melhora a cada correção.\n'
            'Feedback constante = agente cada vez melhor = mais vendas\n'
            'e menos trabalho manual para sua equipe.\n\n'
            'Em caso de dúvidas, entre em contato com o suporte Neuraxo. 🚀'
        ),
        'tempo_estimado': 60,
    },
]


def criar_template(apps, schema_editor):
    ProjetoTemplateGlobal = apps.get_model('tenants', 'ProjetoTemplateGlobal')
    EtapaTemplateGlobal = apps.get_model('tenants', 'EtapaTemplateGlobal')

    template = ProjetoTemplateGlobal.objects.create(
        titulo='Treinamento de Agentes IA - Neuraxo Agents',
        descricao=(
            'Template completo para treinamento de agentes IA para e-commerce.\n'
            '5 fases com guias explicativos detalhados em cada etapa:\n\n'
            '📋 Fase 1: Configuração Base (~50min)\n'
            '📚 Fase 2: Base de Conhecimento (~70min)\n'
            '🎯 Fase 3: Treinamento Interativo (~70min)\n'
            '📊 Fase 4: Métricas e Refinamento (~40min)\n'
            '🚀 Fase 5: Go Live (~95min)\n\n'
            'Tempo total estimado: ~5 horas\n'
            'Cada etapa contém instruções passo a passo com exemplos reais,\n'
            'boas práticas e dicas para treinar o agente da melhor forma.'
        ),
        cor='#8b5cf6',
        ativo=True,
    )

    for etapa_data in ETAPAS:
        EtapaTemplateGlobal.objects.create(template=template, **etapa_data)


def reverter(apps, schema_editor):
    ProjetoTemplateGlobal = apps.get_model('tenants', 'ProjetoTemplateGlobal')
    ProjetoTemplateGlobal.objects.filter(
        titulo='Treinamento de Agentes IA - Neuraxo Agents'
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0004_replace_checklist_with_projeto_template_global'),
    ]

    operations = [
        migrations.RunPython(criar_template, reverter),
    ]
