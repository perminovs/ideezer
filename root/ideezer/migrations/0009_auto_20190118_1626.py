# Generated by Django 2.1.4 on 2019-01-18 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ideezer', '0008_auto_20190113_0545'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='uploadhistory',
            options={'ordering': ['-task__date_done']},
        ),
        migrations.AddField(
            model_name='uploadhistory',
            name='message',
            field=models.CharField(max_length=255, null=True),
        ),
    ]