# Generated by Django 2.1.5 on 2019-01-27 08:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ideezer', '0013_auto_20190127_0820'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deezertrack',
            name='playlists',
        ),
    ]
