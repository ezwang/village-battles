# Generated by Django 2.0 on 2017-12-28 16:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0013_trooptask'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='troop',
            unique_together={('village', 'type')},
        ),
    ]