"""
Views customizadas para o Admin - Documentação do Schema
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.apps import apps
from django.db import models


def superuser_required(view_func):
    """Decorator que exige superuser"""
    decorated_view = user_passes_test(lambda u: u.is_superuser)(view_func)
    return staff_member_required(decorated_view)


@superuser_required
def schema_view(request):
    """View que mostra o schema completo do banco de dados"""

    # Apps para documentar (excluir apps do Django)
    APPS_TO_DOCUMENT = ['core', 'checklists', 'financeiro', 'tenants']
    EXCLUDED_APPS = ['admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles']

    schema_data = []

    for app_config in apps.get_app_configs():
        app_name = app_config.name.split('.')[-1]

        # Filtrar apps
        if app_name in EXCLUDED_APPS:
            continue
        if APPS_TO_DOCUMENT and app_name not in APPS_TO_DOCUMENT:
            continue

        app_models = []

        for model in app_config.get_models():
            model_info = {
                'name': model.__name__,
                'verbose_name': model._meta.verbose_name,
                'verbose_name_plural': model._meta.verbose_name_plural,
                'db_table': model._meta.db_table,
                'docstring': model.__doc__ or '',
                'fields': [],
                'relationships': [],
            }

            # Campos do modelo
            for field in model._meta.get_fields():
                field_info = {
                    'name': field.name,
                    'type': type(field).__name__,
                    'verbose_name': getattr(field, 'verbose_name', field.name),
                    'null': getattr(field, 'null', False),
                    'blank': getattr(field, 'blank', False),
                    'default': None,
                    'choices': None,
                    'help_text': getattr(field, 'help_text', ''),
                    'max_length': getattr(field, 'max_length', None),
                    'related_model': None,
                    'is_relation': field.is_relation,
                }

                # Default value
                if hasattr(field, 'default') and field.default is not models.NOT_PROVIDED:
                    if callable(field.default):
                        field_info['default'] = f"{field.default.__name__}()"
                    else:
                        field_info['default'] = str(field.default)

                # Choices
                if hasattr(field, 'choices') and field.choices:
                    field_info['choices'] = field.choices

                # Related model
                if field.is_relation and hasattr(field, 'related_model') and field.related_model:
                    field_info['related_model'] = field.related_model.__name__
                    model_info['relationships'].append({
                        'field': field.name,
                        'type': type(field).__name__,
                        'to': field.related_model.__name__,
                        'related_name': getattr(field, 'related_query_name', lambda: None)() or 'N/A',
                    })

                # Não incluir relações reversas na lista de campos
                if not (field.is_relation and field.auto_created and not field.concrete):
                    model_info['fields'].append(field_info)

            app_models.append(model_info)

        if app_models:
            schema_data.append({
                'name': app_name,
                'verbose_name': app_config.verbose_name,
                'models': sorted(app_models, key=lambda x: x['name']),
            })

    # Ordenar apps
    schema_data.sort(key=lambda x: x['name'])

    # Estatísticas
    total_models = sum(len(app['models']) for app in schema_data)
    total_fields = sum(
        len(model['fields'])
        for app in schema_data
        for model in app['models']
    )

    context = {
        'title': 'Schema do Banco de Dados',
        'schema_data': schema_data,
        'total_apps': len(schema_data),
        'total_models': total_models,
        'total_fields': total_fields,
    }

    return render(request, 'admin/schema.html', context)
