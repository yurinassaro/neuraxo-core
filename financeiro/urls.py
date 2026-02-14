from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_financeiro, name='dashboard_financeiro'),
    path('lancar/', views.lancar, name='lancar'),
    path('lancamentos/', views.lista_lancamentos, name='lista_lancamentos'),
    path('lancamento/<int:lancamento_id>/excluir/', views.excluir_lancamento, name='excluir_lancamento'),
    path('categorizar-lote/', views.categorizar_lote, name='categorizar_lote'),
    path('metas/', views.gerenciar_metas, name='gerenciar_metas'),
    path('categorias/', views.gerenciar_categorias, name='gerenciar_categorias'),
    path('categorias/por-empresa/<int:empresa_id>/', views.categorias_por_empresa, name='categorias_por_empresa'),
    path('mercadopago/config/', views.config_mercadopago, name='config_mercadopago'),
    path('mercadopago/sync/', views.sync_mercadopago_view, name='sync_mercadopago'),
    path('contas/', views.contas_bancarias, name='contas_bancarias'),
    path('importar-extrato/', views.importar_extrato, name='importar_extrato'),
    path('lancamento/<int:lancamento_id>/prestacao/', views.prestacao_contas, name='prestacao_contas'),
    path('prestacao/<int:prestacao_id>/excluir/', views.excluir_prestacao, name='excluir_prestacao'),
    path('relatorio/', views.relatorio_financeiro, name='relatorio_financeiro'),
    path('registrar-retirada/', views.registrar_retirada, name='registrar_retirada'),
    path('contas-pagar/', views.contas_pagar, name='contas_pagar'),
    path('contas-pagar/pagar/<int:item_id>/', views.pagar_conta, name='pagar_conta'),
    # Contas a Receber
    path('contas-receber/', views.contas_receber, name='contas_receber'),
    path('contas-receber/<int:conta_id>/', views.detalhe_conta_receber, name='detalhe_conta_receber'),
    path('contas-receber/receber/<int:item_id>/', views.receber_conta, name='receber_conta'),
    path('contas-receber/cancelar/<int:item_id>/', views.cancelar_conta_receber, name='cancelar_conta_receber'),
    # Fluxo de Caixa
    path('fluxo-caixa/', views.fluxo_caixa, name='fluxo_caixa'),
    # DRE Simplificado
    path('dre/', views.dre_simplificado, name='dre_simplificado'),
    # Alertas Financeiros
    path('alertas/', views.alertas_financeiros, name='alertas_financeiros'),
    path('alertas/teste/', views.enviar_alerta_teste, name='enviar_alerta_teste'),
    # Relatorio por Projeto
    path('relatorio-projeto/', views.relatorio_projeto, name='relatorio_projeto'),
    # Comparativo Mensal
    path('comparativo/', views.comparativo_mensal, name='comparativo_mensal'),
]
