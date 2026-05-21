"""
URLs para o schema publico (public).
Acessado quando nao ha tenant (ex: core.neuraxo.com.br sem subdomain).
"""
from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from core.admin_views import schema_view


def landing(request):
    """Renderiza a landing page publica"""
    return render(request, 'landing.html')


urlpatterns = [
    path('admin/schema/', schema_view, name='admin_schema'),
    path('admin/', admin.site.urls),
    path('', landing, name='landing'),
]
