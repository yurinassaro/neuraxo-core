from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_pastaempresa_arquivoempresa'),
        ('checklists', '0019_add_horario_sugerido'),
    ]

    operations = [
        migrations.AddField(
            model_name='checklisttemplate',
            name='criado_por',
            field=models.ForeignKey(
                blank=True, null=True,
                help_text='Quem criou esta rotina (gestor ou funcionário)',
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='rotinas_criadas',
                to='core.pessoa',
            ),
        ),
    ]
