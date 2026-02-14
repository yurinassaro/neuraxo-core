from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.admin_views import schema_view

# Customiza o admin
admin.site.site_header = 'NeuraxoCore'
admin.site.site_title = 'NeuraxoCore Admin'
admin.site.index_title = 'Gestão de Rotinas e Projetos'

urlpatterns = [
    # Schema/Escopo do Banco (antes do admin para não conflitar)
    path('admin/schema/', schema_view, name='admin_schema'),
    path('admin/', admin.site.urls),
    path('', include('checklists.urls')),
    path('financeiro/', include('financeiro.urls')),
    path('api/', include('checklists.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None)
