from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


ITUNES = 'itunes'
DEEZER = 'deezer'
source_names = {ITUNES: 'iTunes', DEEZER: 'Deezer'}


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

    class Meta:
        unique_together = (
            ('user', 'itunes_id')
        )

    def get_absolute_url(self):
        return reverse('playlist_detail', args=[self.id])

    def __str__(self):
        return ' | '.join(
            part for part in (self.str_itunes, self.str_deezer) if part
        )

    @property
    def str_itunes(self):
        """ <title> (iTunes <track_cnt>) (<owner_name>) """
        return self.__str(source=ITUNES, with_user=True)

    @property
    def str_deezer(self):
        """ <title> (Deezer <track_cnt>) """
        return self.__str(source=DEEZER, with_user=False)

    def __str(self, source, with_user=False):
        """ Returns part of playlist string representation

        :param source: 'itunes' or 'deezer'
        :param with_user: add playlist owner name to result?
        """
        assert source in (ITUNES, DEEZER)

        _title = getattr(self, source + '_title')
        if not _title:
            return
        _id = getattr(self, source + '_id')
        _content = getattr(self, source + '_content')

        count_section = ''
        if self.id:  # can we use many-to-many relationship?
            count_section = ' ({} {} tracks)'.format(
                _content.count(), source_names[source]
            )
        user_section = ' ({})'.format(self.user) if with_user else ''
        return '{}{}{}'.format(_title, count_section, user_section)

    def save(self, *args, **kwargs):
        err = self.validate()
        if err:
            raise ValueError(err)

        if self.id:  # can we use many-to-many relationship?
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
