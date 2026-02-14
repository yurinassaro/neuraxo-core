from django.urls import path
from . import api_views

urlpatterns = [
    path('webhook/', api_views.webhook_wapi, name='webhook_wapi'),
    path('tarefas/<str:telefone>/', api_views.tarefas_pessoa, name='api_tarefas_pessoa'),
    path('concluir/<int:item_id>/', api_views.api_marcar_concluido, name='api_marcar_concluido'),
]
