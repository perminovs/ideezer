from django.db import models
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


class UserTrack(BaseTrack):
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


class Playlist(models.Model):
    itunes_id = models.IntegerField(null=True, blank=True)
    itunes_title = models.CharField(max_length=255, null=True, blank=True)
    itunes_content = models.ManyToManyField(UserTrack, blank=True)

    deezer_id = models.IntegerField(null=True, blank=True)
    deezer_title = models.CharField(max_length=255, null=True, blank=True)
    deezer_content = models.ManyToManyField(DeezerTrack, blank=True)

    def __str__(self):
        result = []
        if self.itunes_title:
            result.append('{} ({} iTunes tracks)'.format(
                self.itunes_title, self.itunes_content.count()
            ))
        if self.deezer_title:
            result.append('{} ({} Deezer tracks)'.format(
                self.deezer_title, self.deezer_content.count()
            ))
        return ' | '.join(result)

    # TODO validation while save:
    # `itunes_title` and `deezer_title` cannot be NULL together
    # `_title` cannot be NULL if `_id` IS NOT NULL
