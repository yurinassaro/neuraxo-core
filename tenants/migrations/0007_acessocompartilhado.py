from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tenants', '0006_update_whatsapp_business_template'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcessoCompartilhado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_gestor', models.BooleanField(default=False, help_text='Se marcado, o usuário terá permissões de gestor no tenant destino')),
                ('empresas_ids', models.JSONField(blank=True, default=list, help_text='IDs das empresas permitidas no tenant destino (vazio = nenhuma)')),
                ('ativo', models.BooleanField(default=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('tenant_destino', models.ForeignKey(help_text='Tenant que o usuário poderá acessar', on_delete=django.db.models.deletion.CASCADE, related_name='acessos_recebidos', to='tenants.client')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='acessos_compartilhados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Acesso Compartilhado',
                'verbose_name_plural': 'Acessos Compartilhados',
                'unique_together': {('user', 'tenant_destino')},
            },
        ),
    ]
