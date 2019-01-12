from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse


ITUNES = 'itunes'
DEEZER = 'deezer'
source_names = {ITUNES: 'iTunes', DEEZER: 'Deezer'}


class BaseTrack(models.Model):
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


class UploadHistory(models.Model):
    NOT_STARTED = 'NS'
    STARTED = 'ST'
    FAILED = 'FL'
    SUCCESS = 'OK'

    STATUSES = (
        (NOT_STARTED, 'not started'),
        (STARTED, 'started'),
        (FAILED, 'failed'),
        (SUCCESS, 'success'),
    )

    task_id = models.CharField(max_length=255, null=True)

    # TODO fk on celery task model
    start_time = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=2, choices=STATUSES, default=NOT_STARTED)

    tracks_deleted = models.IntegerField(null=True)
    playlists_deleted = models.IntegerField(null=True)
    tracks_created = models.IntegerField(null=True)
    playlists_created = models.IntegerField(null=True)
    error = models.TextField(null=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @classmethod
    def start(cls, task_id, user_id):
        obj = cls(task_id=task_id, user_id=user_id, status=cls.STARTED)
        obj.save()
        return obj

    def mark_failed(self, error):
        self.status = self.FAILED
        self.error = error
        self.save()

    def mark_success(
        self, playlists_deleted, tracks_deleted,
        playlists_created, tracks_created,
    ):
        self.playlists_deleted = playlists_deleted
        self.tracks_deleted = tracks_deleted
        self.playlists_created = playlists_created
        self.tracks_created = tracks_created
        self.status = self.SUCCESS
        self.save()


class UserTrack(BaseTrack):
    itunes_id = models.IntegerField()  # id from iTunes xml
    # `s_`-attribute for track search by Deezer API.
    # By default are the same as attributes without `s_`
    s_title = models.CharField(max_length=255, null=True, blank=True)
    s_artist = models.CharField(max_length=255, null=True, blank=True)
    s_album = models.CharField(max_length=255, null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    objects = _Manager()

    class Meta:
        unique_together = (
            ('user', 'itunes_id')
        )

    def __str__(self):
        return super(UserTrack, self).__str__() + ' ({})'.format(self.user)

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


class TrackIdentity(models.Model):
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


class Playlist(models.Model):
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
        return f'{self.itunes_title} ({self.user})'

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
