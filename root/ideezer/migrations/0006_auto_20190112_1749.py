# Generated by Django 2.1.4 on 2019-01-12 17:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ideezer', '0005_auto_20190112_1731'),
    ]

    operations = [
        migrations.RenameField(
            model_name='uploadhistory',
            old_name='finish_time',
            new_name='last_updated',
        ),
        migrations.AlterField(
            model_name='uploadhistory',
            name='status',
            field=models.CharField(choices=[('NS', 'not started'), ('ST', 'started'), ('FL', 'failed'), ('OK', 'success')], default='NS', max_length=2),
        ),
    ]