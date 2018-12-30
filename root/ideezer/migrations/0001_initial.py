# Generated by Django 2.0.7 on 2018-12-30 18:02

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('deezer_id', models.IntegerField(null=True, unique=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='DeezerTrack',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('artist', models.CharField(max_length=255)),
                ('album', models.CharField(blank=True, max_length=255, null=True)),
                ('deezer_id', models.IntegerField(unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Playlist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('itunes_id', models.IntegerField(blank=True, null=True)),
                ('itunes_title', models.CharField(blank=True, max_length=255, null=True)),
                ('deezer_id', models.IntegerField(blank=True, null=True)),
                ('deezer_title', models.CharField(blank=True, max_length=255, null=True)),
                ('deezer_content', models.ManyToManyField(blank=True, to='ideezer.DeezerTrack')),
            ],
        ),
        migrations.CreateModel(
            name='TrackIdentity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('diff', models.IntegerField()),
                ('choosen', models.NullBooleanField(default=None)),
                ('deezer_track', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ideezer.DeezerTrack')),
            ],
        ),
        migrations.CreateModel(
            name='UserTrack',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('artist', models.CharField(max_length=255)),
                ('album', models.CharField(blank=True, max_length=255, null=True)),
                ('itunes_id', models.IntegerField()),
                ('s_title', models.CharField(blank=True, max_length=255, null=True)),
                ('s_artist', models.CharField(blank=True, max_length=255, null=True)),
                ('s_album', models.CharField(blank=True, max_length=255, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='trackidentity',
            name='user_track',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ideezer.UserTrack'),
        ),
        migrations.AddField(
            model_name='playlist',
            name='itunes_content',
            field=models.ManyToManyField(blank=True, to='ideezer.UserTrack'),
        ),
        migrations.AddField(
            model_name='playlist',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='usertrack',
            unique_together={('user', 'itunes_id')},
        ),
        migrations.AlterUniqueTogether(
            name='trackidentity',
            unique_together={('user_track', 'deezer_track'), ('user_track', 'deezer_track', 'choosen')},
        ),
        migrations.AlterUniqueTogether(
            name='playlist',
            unique_together={('user', 'itunes_id')},
        ),
    ]
