from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_pessoa_user_set_null'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemCofre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200)),
                ('categoria', models.CharField(choices=[('site', 'Site/Sistema'), ('email', 'E-mail'), ('banco', 'Banco/Financeiro'), ('api', 'Chave API'), ('servidor', 'Servidor/Hosting'), ('social', 'Rede Social'), ('outro', 'Outro')], default='site', max_length=20)),
                ('url', models.URLField(blank=True)),
                ('usuario', models.CharField(blank=True, max_length=200)),
                ('senha_encrypted', models.TextField(blank=True, help_text='Senha criptografada')),
                ('notas', models.TextField(blank=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('criado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cofre_criados', to='core.pessoa')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cofre_itens', to='core.empresa')),
            ],
            options={
                'verbose_name': 'Item do Cofre',
                'verbose_name_plural': 'Itens do Cofre',
                'ordering': ['empresa', 'categoria', 'titulo'],
            },
        ),
    ]
