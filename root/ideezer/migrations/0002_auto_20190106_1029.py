# Generated by Django 2.1.4 on 2019-01-06 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ideezer', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deezertrack',
            name='artist',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='playlist',
            name='itunes_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='usertrack',
            name='artist',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]