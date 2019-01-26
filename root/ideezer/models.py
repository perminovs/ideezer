from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django_celery_results.models import TaskResult as CeleryTaskResult
from celery.states import FAILURE


ITUNES = 'itunes'
DEEZER = 'deezer'
source_names = {ITUNES: 'iTunes', DEEZER: 'Deezer'}


class BaseModel(models.Model):
    class Meta:
        abstract = True

    # keep calm and don't show warnings, PyCharm
    # (I just don't have PyCharm Professional, mmkay?)
    objects = models.Manager()


class BaseTrack(BaseModel):
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255, null=True, blank=True)
    album = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        album = ''
        if self.album:
            album = ' (from {})'.format(self.album)
        return '{artist} - {title}{album}'.format(
            artist=self.artist, title=self.title, album=album
        )


class _Manager(models.Manager):
    def by_user(self, user_id):
        return self.filter(user_id=user_id)

    def by_duser(self, duser_id):
        return self.filter(user__deezer_id=duser_id)


class User(AbstractUser):
    # nullable because admin may has no deezer_id
    deezer_id = models.IntegerField(unique=True, null=True)

    def __str__(self):
        return self.username or f'Deezer user #{self.deezer_id}'


class UploadHistory(BaseModel):
    tracks_deleted = models.IntegerField(null=True)
    playlists_deleted = models.IntegerField(null=True)
    tracks_created = models.IntegerField(null=True)
    playlists_created = models.IntegerField(null=True)
    message = models.CharField(max_length=255, null=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.OneToOneField(
        CeleryTaskResult, on_delete=models.CASCADE, unique=True,
    )

    objects = _Manager()

    DEFAULT_ERROR_MESSAGE = 'Server error'

    class Meta:
        ordering = ['-task__date_done']

    @classmethod
    def create(cls, task_id, user_id):
        task = CeleryTaskResult.objects.get_task(task_id=task_id)
        obj = cls(task=task, user_id=user_id)
        obj.save()
        return obj

    def update_info(
        self, playlists_deleted, tracks_deleted,
        playlists_created, tracks_created,
    ):
        self.playlists_deleted = playlists_deleted
        self.tracks_deleted = tracks_deleted
        self.playlists_created = playlists_created
        self.tracks_created = tracks_created
        self.save()

    @property
    def error(self):
        if self.task.status == FAILURE:
            return self.message or self.DEFAULT_ERROR_MESSAGE


class UserTrack(BaseTrack):
    itunes_id = models.IntegerField()  # id from iTunes xml
    # `s_`-attribute for track search by Deezer API.
    _s_title = models.CharField(db_column='s_title', max_length=255, null=True, blank=True)
    _s_artist = models.CharField(db_column='s_artist', max_length=255, null=True, blank=True)
    _s_album = models.CharField(db_column='s_album', max_length=255, null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    objects = _Manager()

    class Meta:
        unique_together = (
            ('user', 'itunes_id')
        )

    def get_absolute_url(self):
        return f'track/{self.pk}'

    @property
    def s_title(self):
        return self._s_title or self.title

    @property
    def s_artist(self):
        return self._s_artist or self.artist

    @property
    def s_album(self):
        return self._s_album or self.album

    def get_absolute_url(self):
        return reverse('track_detail', args=[self.pk])

    @classmethod
    def from_itunes(cls, track, user_id):
        return cls(
            itunes_id=track.track_id,
            title=track.name,
            artist=track.artist,
            album=track.album,
            user_id=user_id,
        )


class DeezerTrack(BaseTrack):
    deezer_id = models.IntegerField(unique=True)

    @classmethod
    def from_deezer(cls, track_info):
        return cls(
            deezer_id=track_info['id'],
            title=track_info['title'],
            artist=track_info['artist']['name'],
            album=track_info['album']['title'],
        )


class TrackIdentity(BaseModel):
    """ How iTunes track is similar to Deezer one.
    """
    user_track = models.ForeignKey(UserTrack, on_delete=models.CASCADE)
    deezer_track = models.ForeignKey(DeezerTrack, on_delete=models.CASCADE)
    diff = models.IntegerField()
    # pair `user_track` to `deezer_track` mark as best (correct)
    choosen = models.NullBooleanField(null=True, default=None, blank=True)

    class Meta:
        unique_together = (
            ('user_track', 'deezer_track'),
            ('user_track', 'deezer_track', 'choosen'),
        )


class Playlist(BaseModel):
    itunes_id = models.IntegerField(null=True, blank=True)
    itunes_persistent_id = models.CharField(max_length=255, null=True, blank=True)
    itunes_title = models.CharField(max_length=255, null=True, blank=True)
    itunes_content = models.ManyToManyField(UserTrack, blank=True)

    # denormalization
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    deezer_id = models.IntegerField(null=True, blank=True)
    deezer_title = models.CharField(max_length=255, null=True, blank=True)
    deezer_content = models.ManyToManyField(DeezerTrack, blank=True)

    objects = _Manager()

    class Meta:
        unique_together = (
            ('user', 'itunes_id')
        )

    def get_absolute_url(self):
        return reverse('playlist_detail', args=[self.pk])

    @classmethod
    def from_itunes(cls, playlist, user_id):
        return cls(
            itunes_id=playlist.playlist_id,
            itunes_persistent_id=playlist.playlist_persistent_id,
            user_id=user_id,
            itunes_title=playlist.name,
        )

    def __str__(self):
        itunes = ''
        if self.itunes_title:
            itunes = f'{self.itunes_title} ({self.itunes_content.count()})'

        deezer = ''
        if self.deezer_title:
            deezer = f'{self.deezer_title} ({self.deezer_content.count()})'

        return f'{itunes} {deezer}'

    def save(self, *args, **kwargs):
        err = self.validate()
        if err:
            raise ValueError(err)

        if self.pk:  # can we use many-to-many relationship?
            # Check playlist contains only tracks from playlist.user
            # Does not work, when saving from admin interface
            for itunes_track in self.itunes_content.all():
                if itunes_track.user != self.user:
                    err = 'Playlist tracks must belongs to playlist User'
                    raise ValueError(err)
        return super(Playlist, self).save(*args, **kwargs)

    def validate(self):
        """ 'Interface' validation. Check playlist attribute is correct

        :return error text if incorrect, None otherwise
        """
        # If iTunes/Deezer id is filled, its title must be filled too.
        for attr1, attr2, name1, name2, in (
            (self.itunes_id, self.itunes_title, 'itunes_id', 'itunes_title'),
            (self.deezer_id, self.deezer_title, 'deezer_id', 'deezer_title'),
        ):
            err = self.validate_xor(attr1, attr2, name1, name2)
            if err:
                return err

        if not self.itunes_title and not self.deezer_title:
            return 'Playlist title cannot be None'

    @staticmethod
    def validate_xor(attr1, attr2, name1, name2):
        if bool(attr1) != bool(attr2):
            return (
                '{name1} and {name2} attributes must be `None` or `not None` '
                'together. Got {name1} = `{value1}` and {name2} = `{value2}` '
                'instead'.format(
                    name1=name1, name2=name2, value1=attr1, value2=attr2,
                ))
