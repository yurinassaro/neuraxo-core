"""
URLs para o schema público (public).
Acessado quando não há tenant (ex: core.neuraxo.com.br sem subdomain).
"""
from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from tenants.views import api_empresas_tenant


def landing(request):
    """Exibe landing page no schema público"""
    return render(request, 'landing.html')


def login_redirect(request):
    """Redireciona /login/ para /admin/login/ no schema público"""
    return redirect('/admin/login/')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/tenant/<int:tenant_id>/empresas/', api_empresas_tenant, name='api_empresas_tenant'),
    path('login/', login_redirect, name='login'),
    path('', landing, name='landing'),
]
