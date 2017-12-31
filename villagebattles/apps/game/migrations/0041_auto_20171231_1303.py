# Generated by Django 2.0 on 2017-12-31 18:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('game', '0040_auto_20171231_1233'),
    ]

    operations = [
        migrations.CreateModel(
            name='Quest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed', models.BooleanField(default=False)),
                ('type', models.PositiveSmallIntegerField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='all_quests', to=settings.AUTH_USER_MODEL)),
                ('world', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.World')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='quest',
            unique_together={('user', 'world', 'type')},
        ),
    ]