# Generated by Django 2.0 on 2017-12-28 16:12

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0012_auto_20171228_1026'),
    ]

    operations = [
        migrations.CreateModel(
            name='TroopTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('SP', 'Spearman'), ('AX', 'Axeman')], max_length=2)),
                ('amount', models.IntegerField()),
                ('start_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('end_time', models.DateTimeField(null=True)),
                ('village', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='troopqueue', to='game.Village')),
            ],
        ),
    ]