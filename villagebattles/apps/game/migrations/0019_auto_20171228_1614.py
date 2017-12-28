# Generated by Django 2.0 on 2017-12-28 21:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0018_report'),
    ]

    operations = [
        migrations.AddField(
            model_name='attack',
            name='loot',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to=settings.AUTH_USER_MODEL),
        ),
    ]
