# Generated by Django 2.0 on 2017-12-28 03:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0005_auto_20171228_0238'),
    ]

    operations = [
        migrations.AlterField(
            model_name='building',
            name='type',
            field=models.CharField(choices=[('HQ', 'Headquarters'), ('WM', 'Wood Mine'), ('CM', 'Clay Mine'), ('IM', 'Iron Mine'), ('WH', 'Warehouse'), ('FM', 'Farm')], default='HQ', max_length=2),
        ),
    ]
