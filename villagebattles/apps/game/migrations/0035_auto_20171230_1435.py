# Generated by Django 2.0 on 2017-12-30 19:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0034_auto_20171230_1424'),
    ]

    operations = [
        migrations.AlterField(
            model_name='troop',
            name='type',
            field=models.CharField(choices=[('AR', 'Archer'), ('AX', 'Axeman'), ('NB', 'Noble'), ('SC', 'Scout'), ('SP', 'Spearman'), ('SW', 'Swordsman')], max_length=2),
        ),
        migrations.AlterField(
            model_name='trooptask',
            name='type',
            field=models.CharField(choices=[('AR', 'Archer'), ('AX', 'Axeman'), ('NB', 'Noble'), ('SC', 'Scout'), ('SP', 'Spearman'), ('SW', 'Swordsman')], max_length=2),
        ),
    ]
