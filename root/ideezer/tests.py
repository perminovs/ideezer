from random import randint
import uuid

from django.test import TestCase

from . import models as md


def strand(length=None):
    return uuid.uuid4().hex[:length]


def intrand(minimum=0, maximum=1000000):
    return randint(a=minimum, b=maximum)


def create_user_track(user):
    return md.UserTrack.objects.create(
        itunes_id=intrand(), title=strand(), artist=strand(), user=user
    )


def create_playlist(user):
    return md.Playlist.objects.create(
        itunes_title=strand(), itunes_id=intrand(), user=user
    )


class PlaylistTestCase(TestCase):
    def setUp(self):
        self.user1 = md.User.objects.create_user(strand())
        self.user2 = md.User.objects.create_user(strand())
        # tracks belong to one user
        self.consistent_tracks = [
            create_user_track(self.user1), create_user_track(self.user1)
        ]
        # tracks belong to defferent users
        self.unconsistent_tracks = [
            create_user_track(self.user1), create_user_track(self.user2)
        ]

    # #######################
    # Not NULL attribute test
    # #######################

    def test_no_title_err(self):
        with self.assertRaisesMessage(
            ValueError, 'Playlist title cannot be None'
        ):
            md.Playlist.objects.create(user=self.user1)

    def test_consistency_err_itunes1(self):
        with self.assertRaises(ValueError):
            md.Playlist.objects.create(itunes_id=intrand(), user=self.user1)

    def test_consistency_err_itunes2(self):
        with self.assertRaises(ValueError):
            md.Playlist.objects.create(itunes_title=strand(), user=self.user1)

    def test_consistency_err_deezer1(self):
        with self.assertRaises(ValueError):
            md.Playlist.objects.create(deezer_id=intrand(), user=self.user1)

    def test_consistency_err_deezer2(self):
        with self.assertRaises(ValueError):
            md.Playlist.objects.create(deezer_title=strand(), user=self.user1)

    # #######################
    # Playlist content tests
    # #######################

    def test_content_ok(self):
        plst = create_playlist(user=self.user1)
        plst.itunes_content.add(*[track for track in self.consistent_tracks])
        plst.save()

    def test_content_err(self):
        plst = create_playlist(user=self.user1)
        plst.itunes_content.add(*[track for track in self.unconsistent_tracks])
        with self.assertRaisesMessage(
            ValueError, 'Playlist tracks must belongs to playlist User'
        ):
            plst.save()
