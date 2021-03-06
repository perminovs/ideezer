from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django_celery_results.models import TaskResult as CeleryTaskResult
from celery.states import FAILURE
import Levenshtein


ITUNES = 'itunes'
DEEZER = 'deezer'
source_names = {ITUNES: 'iTunes', DEEZER: 'Deezer'}


class BaseModel(models.Model):
    class Meta:
        abstract = True

    # keep calm and don't show warnings, PyCharm
    # (I just don't have PyCharm Professional, mmkay?)
    objects = models.Manager()

    @classmethod
    def create_or_update(cls, **kwargs):
        obj = cls._search(**kwargs)
        if obj:
            return obj

        return cls._create(**kwargs)

    @classmethod
    def _search(cls, **kwargs):
        obj = cls.objects.filter(**kwargs).first()
        if obj:
            return obj

    @classmethod
    def _create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()
        return obj


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
    deezer_id = models.BigIntegerField(unique=True, null=True)

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
    itunes_id = models.BigIntegerField()  # id from iTunes xml
    # `s_`-attribute for track search by Deezer API.
    _s_title = models.CharField(db_column='s_title', max_length=255, null=True, blank=True)
    _s_artist = models.CharField(db_column='s_artist', max_length=255, null=True, blank=True)
    _s_album = models.CharField(db_column='s_album', max_length=255, null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    identities = models.ManyToManyField('DeezerTrack', through='TrackIdentity')
    playlists = models.ManyToManyField('Playlist')

    objects = _Manager()

    class Meta:
        unique_together = (
            ('user', 'itunes_id')
        )

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
        return reverse('track_edit', args=[self.pk])

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
    deezer_id = models.BigIntegerField(unique=True)

    @classmethod
    def from_deezer(cls, track_info):
        deezer_id = track_info['id']
        obj = cls.objects.filter(deezer_id=deezer_id).first()
        if obj:
            return obj

        obj = cls(
            deezer_id=deezer_id,
            title=track_info['title'],
            artist=track_info['artist']['name'],
            album=track_info['album']['title'],
        )
        obj.save()
        return obj


class TrackIdentity(BaseModel):
    """ How iTunes track is similar to Deezer one.
    """
    user_track = models.ForeignKey(UserTrack, on_delete=models.CASCADE)
    deezer_track = models.ForeignKey(DeezerTrack, on_delete=models.CASCADE)
    diff = models.IntegerField()
    # pair `user_track` to `deezer_track` mark as best (correct)
    chosen = models.NullBooleanField(null=True, default=None, blank=True)

    class Meta:
        unique_together = (
            ('user_track', 'deezer_track'),
        )

    def save(
        self, force_insert=False, force_update=False,
        using=None, update_fields=None
    ):
        exists = type(self).objects.filter(
            user_track=self.user_track, chosen=True,
        ).first()  # FIXME можно сделать всё в запросе
        if exists and self.chosen and exists.id != self.id:
            raise ValueError(f'Duplicate entry for chosen track: {self.user_track}')

        return super(TrackIdentity, self).save(
            force_insert=force_insert, force_update=force_update,
            using=using, update_fields=update_fields)

    @classmethod
    def _create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.set_diff()
        obj.save()
        return obj

    def set_diff(self):
        self.diff = 0
        for attr1, attr2 in zip(
            (self.user_track.s_artist, self.user_track.s_title),
            (self.deezer_track.artist, self.deezer_track.title),
        ):
            self.diff += Levenshtein.distance(attr1, attr2)

        if self.user_track.s_album:
            self.diff += Levenshtein.distance(
                self.user_track.s_album, self.deezer_track.album
            )

    @classmethod
    def mark_exists_track_as_pair(cls, user_track):  # TODO move to controller
        """ Returns True when:
            * `user_track` already has a `chosen` deezer pair;
            * `user_track` has a set of available pairs without `chosen`. In
            this case also mark best candidate for pair as `chosen`.

            Return None otherwise.
        """
        if cls.objects.filter(user_track=user_track, chosen=True).first():
            return True

        pair = cls.objects.filter(
            user_track=user_track,
        ).order_by('-diff').first()
        if pair:
            pair.chosen = True
            pair.save()
            return True


class Playlist(BaseModel):
    itunes_id = models.BigIntegerField()
    itunes_persistent_id = models.CharField(max_length=255)
    itunes_title = models.CharField(max_length=255)
    itunes_content = models.ManyToManyField(UserTrack, blank=True)

    # denormalization
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    deezer_id = models.BigIntegerField(null=True, blank=True)
    deezer_title = models.CharField(max_length=255, null=True, blank=True)

    objects = _Manager()

    class Meta:
        unique_together = (
            ('user', 'itunes_id')
        )
        ordering = ['itunes_title']

    def get_absolute_url(self):
        return reverse('playlist_detail', args=[self.pk])

    @property
    def identities(self):
        return TrackIdentity.objects.filter(
            chosen=True
        ).filter(
            user_track__playlist=self
        )

    @property
    def unpaired(self):
        empty_ideinity = self.itunes_content.filter(identities__isnull=True)
        non_chosen = self.itunes_content.filter(trackidentity__chosen=False)
        # todo remove duplicates
        return empty_ideinity | non_chosen

    @classmethod
    def from_itunes(cls, playlist, user_id):
        return cls(
            itunes_id=playlist.playlist_id,
            itunes_persistent_id=playlist.playlist_persistent_id,
            user_id=user_id,
            itunes_title=playlist.name,
        )

    def __str__(self):
        itunes = f'{self.itunes_title} ({self.itunes_content.count()})'

        if not self.deezer_id:
            return itunes

        deezer = f'{self.deezer_title} ({self.identities.count()})'
        return f'{itunes} | {deezer}'

    def save(self, *args, **kwargs):
        # Validations does not work, when saving from admin interface

        # deezer consistency check
        if bool(self.deezer_id) != bool(self.deezer_title):
            err = (
                f'deezer_id and deezer_title attributes must be `None` or'
                f'`not None` together. Got deezer_id = {self.deezer_id} and '
                f'deezer_title = {self.deezer_title} instead'
            )
            raise ValueError(err)

        # check playlist contains only tracks from playlist.user
        if self.pk:
            for itunes_track in self.itunes_content.all():
                if itunes_track.user != self.user:
                    err = 'Playlist tracks must belongs to playlist User'
                    raise ValueError(err)
        return super(Playlist, self).save(*args, **kwargs)
