# Generated by Django 2.0 on 2017-12-31 17:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0039_auto_20171231_1201'),
    ]

    operations = [
        migrations.AlterField(
            model_name='troop',
            name='type',
            field=models.CharField(choices=[('AR', 'Archer'), ('AX', 'Axeman'), ('CA', 'Catapult'), ('CM', 'Calvaryman'), ('KN', 'Knight'), ('NB', 'Noble'), ('SC', 'Scout'), ('SP', 'Spearman'), ('SW', 'Swordsman')], max_length=2),
        ),
        migrations.AlterField(
            model_name='trooptask',
            name='type',
            field=models.CharField(choices=[('AR', 'Archer'), ('AX', 'Axeman'), ('CA', 'Catapult'), ('CM', 'Calvaryman'), ('KN', 'Knight'), ('NB', 'Noble'), ('SC', 'Scout'), ('SP', 'Spearman'), ('SW', 'Swordsman')], max_length=2),
        ),
    ]
