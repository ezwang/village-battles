# Generated by Django 2.0 on 2017-12-28 04:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0009_buildtask'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='buildtask',
            name='start_time',
        ),
        migrations.AddField(
            model_name='buildtask',
            name='end_time',
            field=models.DateTimeField(null=True),
        ),
    ]
