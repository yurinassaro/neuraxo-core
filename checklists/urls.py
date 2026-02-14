from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Rotina Diária
    path('rotina/', views.rotina_diaria, name='rotina_diaria'),
    path('tarefas/', views.minhas_tarefas, name='minhas_tarefas'),  # Alias
    path('tarefa/<int:item_id>/', views.detalhe_tarefa, name='detalhe_tarefa'),
    path('concluir/<int:item_id>/', views.marcar_concluido, name='marcar_concluido'),
    path('iniciar/<int:item_id>/', views.marcar_em_andamento, name='marcar_em_andamento'),
    path('processo/<int:template_id>/', views.ver_processo, name='ver_processo'),
    path('relatorio/<int:workspace_id>/', views.relatorio_workspace, name='relatorio_workspace'),

    # Timer (Rotina)
    path('timer/iniciar/<int:item_id>/', views.timer_iniciar, name='timer_iniciar'),
    path('timer/pausar/<int:item_id>/', views.timer_pausar, name='timer_pausar'),
    path('timer/status/<int:item_id>/', views.timer_status, name='timer_status'),
    path('timer/editar/<int:item_id>/', views.timer_tarefa_editar, name='timer_tarefa_editar'),

    # Anotações (Rotina)
    path('salvar-anotacao/<int:item_id>/', views.salvar_anotacao, name='salvar_anotacao'),

    # Subtarefas (Rotina)
    path('subtarefa/adicionar/<int:item_id>/', views.adicionar_subtarefa, name='adicionar_subtarefa'),
    path('subtarefa/toggle/<int:subtarefa_id>/', views.toggle_subtarefa, name='toggle_subtarefa'),
    path('subtarefa/excluir/<int:subtarefa_id>/', views.excluir_subtarefa, name='excluir_subtarefa'),
    path('subtarefa/sincronizar/<int:item_id>/', views.sincronizar_subtarefas, name='sincronizar_subtarefas'),

    # Status e Dependência (Rotina)
    path('status/<int:item_id>/', views.mudar_status, name='mudar_status'),
    path('dependencia/<int:item_id>/', views.marcar_dependente, name='marcar_dependente'),
    path('cancelar/<int:item_id>/', views.cancelar_tarefa, name='cancelar_tarefa'),
    path('excluir-tarefa/<int:item_id>/', views.excluir_tarefa, name='excluir_tarefa'),
    path('cancelar/<int:item_id>/aprovar/', views.aprovar_cancelamento, name='aprovar_cancelamento'),
    path('cancelar/<int:item_id>/recusar/', views.recusar_cancelamento, name='recusar_cancelamento'),
    path('pausar/<int:item_id>/', views.pausar_tarefa, name='pausar_tarefa'),
    path('despausar/<int:item_id>/', views.despausar_tarefa, name='despausar_tarefa'),
    path('pessoas/', views.listar_pessoas, name='listar_pessoas'),
    path('pessoas/<int:empresa_id>/', views.listar_pessoas_empresa, name='listar_pessoas_empresa'),
    path('pessoas-externas/', views.buscar_pessoas_externas, name='buscar_pessoas_externas'),

    # ============================================
    # DEMANDAS / PENDÊNCIAS
    # ============================================
    path('demandas/', views.lista_demandas, name='lista_demandas'),
    path('demandas/nova/', views.criar_demanda, name='criar_demanda'),
    path('demanda/<int:demanda_id>/', views.detalhe_demanda, name='detalhe_demanda'),
    path('demanda/<int:demanda_id>/editar/', views.editar_demanda, name='editar_demanda'),
    path('demanda/<int:demanda_id>/status/', views.mudar_status_demanda, name='mudar_status_demanda'),
    path('demanda/<int:demanda_id>/reabrir/', views.reabrir_demanda, name='reabrir_demanda'),

    # Timer (Demanda)
    path('demanda/<int:demanda_id>/timer/iniciar/', views.timer_demanda_iniciar, name='timer_demanda_iniciar'),
    path('demanda/<int:demanda_id>/timer/pausar/', views.timer_demanda_pausar, name='timer_demanda_pausar'),
    path('demanda/<int:demanda_id>/timer/editar/', views.timer_demanda_editar, name='timer_demanda_editar'),

    # Anotações e Comentários (Demanda)
    path('demanda/<int:demanda_id>/anotacao/', views.salvar_anotacao_demanda, name='salvar_anotacao_demanda'),
    path('demanda/<int:demanda_id>/comentario/', views.adicionar_comentario_demanda, name='adicionar_comentario_demanda'),

    # Anexos (Demanda)
    path('demanda/<int:demanda_id>/anexo/', views.upload_anexo_demanda, name='upload_anexo_demanda'),
    path('anexo/<int:anexo_id>/excluir/', views.excluir_anexo_demanda, name='excluir_anexo_demanda'),

    # Subtarefas (Demanda)
    path('demanda/<int:demanda_id>/subtarefa/', views.adicionar_subtarefa_demanda, name='adicionar_subtarefa_demanda'),
    path('demanda/subtarefa/<int:subtarefa_id>/toggle/', views.toggle_subtarefa_demanda, name='toggle_subtarefa_demanda'),
    path('demanda/subtarefa/<int:subtarefa_id>/excluir/', views.excluir_subtarefa_demanda, name='excluir_subtarefa_demanda'),

    # Dependência (Demanda)
    path('demanda/<int:demanda_id>/dependencia/', views.marcar_dependente_demanda, name='marcar_dependente_demanda'),
    path('demanda/<int:demanda_id>/excluir/', views.excluir_demanda, name='excluir_demanda'),

    # ============================================
    # PROJETOS
    # ============================================
    path('projetos/', views.lista_projetos, name='lista_projetos'),
    path('projetos/templates/', views.lista_templates, name='lista_templates'),
    path('projetos/templates/<int:template_id>/mapa/', views.mapa_mental_template, name='mapa_mental_template'),
    path('projetos/novo/', views.criar_projeto, name='criar_projeto'),
    path('projeto/<int:projeto_id>/', views.detalhe_projeto, name='detalhe_projeto'),
    path('projeto/<int:projeto_id>/etapa/', views.adicionar_etapa_projeto, name='adicionar_etapa_projeto'),
    path('projeto/<int:projeto_id>/status/', views.mudar_status_projeto, name='mudar_status_projeto'),
    path('projeto/<int:projeto_id>/excluir/', views.excluir_projeto, name='excluir_projeto'),
    path('etapa/<int:demanda_id>/excluir/', views.excluir_etapa_projeto, name='excluir_etapa_projeto'),
    path('projeto/<int:projeto_id>/participantes/', views.gerenciar_participantes_projeto, name='gerenciar_participantes_projeto'),
    path('projeto/<int:projeto_id>/mapa/', views.mapa_mental_projeto, name='mapa_mental_projeto'),
    path('projeto/<int:projeto_id>/mapa/no/', views.adicionar_no_mapa, name='adicionar_no_mapa'),
    path('projeto/mapa/no/<int:no_id>/excluir/', views.excluir_no_mapa, name='excluir_no_mapa'),
    path('projeto/mapa/no/<int:no_id>/editar/', views.editar_no_mapa, name='editar_no_mapa'),

    # Justificativa, Acompanhamento e Aproveitamento
    path('justificativa/<int:item_id>/', views.salvar_justificativa, name='salvar_justificativa'),
    path('acompanhamento/', views.acompanhamento, name='acompanhamento'),
    path('aproveitamento/', views.aproveitamento, name='aproveitamento'),
    path('aproveitamento/<str:data_str>/', views.aproveitamento_dia, name='aproveitamento_dia'),
    path('pendentes-justificativa/', views.tarefas_pendentes_justificativa, name='pendentes_justificativa'),

    # WAPI - WhatsApp Integration
    path('wapi/', views.wapi_painel, name='wapi_painel'),
    path('wapi/status/', views.wapi_status, name='wapi_status'),
    path('wapi/teste/', views.wapi_enviar_teste, name='wapi_enviar_teste'),
    path('wapi/cobrar/', views.wapi_cobrar_dependencia, name='wapi_cobrar_dependencia'),
    path('wapi/cobrar-todos/', views.wapi_cobrar_todos, name='wapi_cobrar_todos'),
    path('wapi/agendamentos/', views.wapi_salvar_agendamentos, name='wapi_salvar_agendamentos'),
    path('wapi/executar/', views.wapi_executar_agendamento, name='wapi_executar_agendamento'),

    # Rotinas (CRUD ChecklistTemplate) - Gestores
    path('rotinas/', views.lista_rotinas, name='lista_rotinas'),
    path('rotinas/nova/', views.criar_rotina, name='criar_rotina'),
    path('rotinas/<int:template_id>/editar/', views.editar_rotina, name='editar_rotina'),

    # Calendário
    path('calendario/', views.calendario, name='calendario'),
    path('api/calendario/eventos/', views.calendario_eventos, name='calendario_eventos'),

    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='checklists/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
