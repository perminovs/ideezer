from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class BaseTrack(models.Model):
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    album = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        album = ''
        if self.album:
            album = '(from {})'.format(self.album)
        return '{artist} - {title}{album}'.format(
            artist=self.artist, title=self.title, album=album
        )


class UserFilterModelMixin:
    @classmethod
    def by_user(cls, user):
        user = user if user.is_authenticated else None
        return cls.objects.filter(user=user)


class UserTrack(BaseTrack, UserFilterModelMixin):
    itunes_id = models.IntegerField()  # id from iTunes xml
    # `s_`-attribute for track search by Deezer API.
    # By default are the same as attributes without `s_`
    s_title = models.CharField(max_length=255, null=True, blank=True)
    s_artist = models.CharField(max_length=255, null=True, blank=True)
    s_album = models.CharField(max_length=255, null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('user', 'itunes_id')
        )

    def __str__(self):
        return super(UserTrack, self).__str__() + ' ({})'.format(self.user)

    def get_absolute_url(self):
        return reverse('track_detail', args=[self.id])


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
            ('user_track', 'deezer_track', 'choosen')
        )


class Playlist(models.Model, UserFilterModelMixin):
    itunes_id = models.IntegerField(null=True, blank=True)
    itunes_title = models.CharField(max_length=255, null=True, blank=True)
    itunes_content = models.ManyToManyField(UserTrack, blank=True)

    # denormalization
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    deezer_id = models.IntegerField(null=True, blank=True)
    deezer_title = models.CharField(max_length=255, null=True, blank=True)
    deezer_content = models.ManyToManyField(DeezerTrack, blank=True)

    def get_absolute_url(self):
        return reverse('playlist_detail', args=[self.id])

    def __str__(self):
        return ' | '.join(part for part in (
            self.str_itunes(), self.str_deezer()
        ) if part)

    def str_itunes(self):
        if self.itunes_title:
            return '{} ({} iTunes tracks) ({})'.format(
                self.itunes_title, self.itunes_content.count(),
                self.user,
            )

    def str_deezer(self):
        if self.deezer_title:
            return '{} ({} Deezer tracks)'.format(
                self.deezer_title, self.deezer_content.count(),
            )

    # TODO validation while save:
    # `itunes_title` and `deezer_title` cannot be NULL together
    # `{}_title` cannot be NULL if `{}_id` IS NOT NULL
