# Generated by Django 2.0 on 2017-12-28 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0014_auto_20171228_1117'),
    ]

    operations = [
        migrations.AlterField(
            model_name='troop',
            name='type',
            field=models.CharField(choices=[('SP', 'Spearman'), ('SW', 'Swordsman'), ('AX', 'Axeman')], default='SP', max_length=2),
        ),
        migrations.AlterField(
            model_name='trooptask',
            name='type',
            field=models.CharField(choices=[('SP', 'Spearman'), ('SW', 'Swordsman'), ('AX', 'Axeman')], max_length=2),
        ),
    ]
