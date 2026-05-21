from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_pastaempresa_arquivoempresa'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemcofre',
            name='compartilhado_com',
            field=models.ManyToManyField(
                blank=True,
                help_text='Funcionarios que podem ver este item (vazio = somente criador e gestores)',
                related_name='cofre_compartilhados',
                to='core.pessoa',
            ),
        ),
    ]
