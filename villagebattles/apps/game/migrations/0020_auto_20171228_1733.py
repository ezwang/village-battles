# Generated by Django 2.0 on 2017-12-28 22:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0019_auto_20171228_1614'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='troop',
            options={'ordering': ['type']},
        ),
        migrations.AddField(
            model_name='report',
            name='read',
            field=models.BooleanField(default=False),
        ),
    ]
