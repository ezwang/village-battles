# Generated by Django 2.0 on 2017-12-29 22:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0028_auto_20171229_1727'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='troop',
            unique_together={('village', 'type', 'original')},
        ),
    ]