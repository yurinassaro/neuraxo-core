# Generated manually for parcelamento

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0009_simplify_conta_pagar'),
    ]

    operations = [
        migrations.AddField(
            model_name='contapagar',
            name='parcelado',
            field=models.BooleanField(default=False, help_text='Se é uma compra parcelada'),
        ),
        migrations.AddField(
            model_name='contapagar',
            name='total_parcelas',
            field=models.IntegerField(default=1, help_text='Número total de parcelas'),
        ),
        migrations.AddField(
            model_name='contapagar',
            name='valor_total',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Valor total da compra (quando parcelado)', max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='contapagaritem',
            name='parcela_numero',
            field=models.IntegerField(blank=True, help_text='Número da parcela (1, 2, 3...)', null=True),
        ),
        migrations.AlterField(
            model_name='contapagar',
            name='recorrencia',
            field=models.CharField(choices=[('unica', 'Única (sem recorrência)'), ('parcelada', 'Parcelada'), ('diaria', 'Diária'), ('semanal', 'Semanal'), ('quinzenal', 'Quinzenal'), ('mensal', 'Mensal'), ('trimestral', 'Trimestral'), ('semestral', 'Semestral'), ('anual', 'Anual')], default='mensal', max_length=12),
        ),
        migrations.AlterModelOptions(
            name='contapagaritem',
            options={'ordering': ['data_vencimento'], 'verbose_name': 'Item Conta a Pagar', 'verbose_name_plural': 'Itens Contas a Pagar'},
        ),
        migrations.AlterUniqueTogether(
            name='contapagaritem',
            unique_together=set(),
        ),
    ]
