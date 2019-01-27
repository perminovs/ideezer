# Generated by Django 2.1.5 on 2019-01-27 08:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ideezer', '0012_auto_20190126_1838'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='playlist',
            name='deezer_content',
        ),
        migrations.AddField(
            model_name='deezertrack',
            name='playlists',
            field=models.ManyToManyField(to='ideezer.Playlist'),
        ),
        migrations.AddField(
            model_name='usertrack',
            name='identities',
            field=models.ManyToManyField(through='ideezer.TrackIdentity', to='ideezer.DeezerTrack'),
        ),
        migrations.AddField(
            model_name='usertrack',
            name='playlists',
            field=models.ManyToManyField(to='ideezer.Playlist'),
        ),
    ]