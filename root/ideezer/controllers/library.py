import logging
from tempfile import NamedTemporaryFile
from plistlib import InvalidFileException

from libpytunes import Library, Playlist

from .. import models as md


logger = logging.getLogger(__name__)


def timeit(func):  # TODO remove debug deco
    from datetime import datetime

    def _inner(*args, **kwargs):
        start = datetime.now()
        res = func(*args, **kwargs)
        logger.info('%s: %s', func.__name__, datetime.now() - start)
        return res
    return _inner


def save(file, user):
    with NamedTemporaryFile(delete=False) as tmp:
        for chunk in file.chunks():
            tmp.write(chunk)

    process(path=tmp.name, user_id=user.id)


def process(path, user_id):
    logger.info('process file: %s for user %s', path, user_id)

    try:
        lib = Library(itunesxml=path)
    except InvalidFileException as ife:
        logger.warning('process error: %s', ife)
        return

    clear_user_itunes_data(user_id)  # TODO merge playlist?
    insert_tracks(lib, user_id)
    insert_playlists(lib, user_id)


@timeit
def clear_user_itunes_data(user_id):
    md.Playlist.objects.by_user(user_id).delete()
    md.UserTrack.objects.by_user(user_id).delete()


@timeit
def insert_tracks(lib, user_id):
    tracks = (
        md.UserTrack.from_itunes(track, user_id)
        for track in lib.songs.values()
    )
    md.UserTrack.objects.bulk_create(tracks)


@timeit
def insert_playlists(lib, user_id):
    tracks_cache = {
        track.itunes_id: track
        for track in md.UserTrack.objects.by_user(user_id)
    }

    for idx, plst_name in enumerate(lib.getPlaylistNames(), start=1):
        plst: Playlist = lib.getPlaylist(plst_name)
        if plst.is_folder or plst.distinguished_kind:
            logger.info(
                'skip `%s` because is_folder = %s, distinguished_kind = %s',
                plst_name, plst.is_folder, plst.distinguished_kind)
            continue

        playlist = md.Playlist.from_itunes(plst, user_id)
        playlist.save()

        content = [tracks_cache[track.track_id] for track in plst.tracks]
        playlist.itunes_content.add(*content)
        playlist.save()

        if idx % 10 == 0:
            logger.info('iter: %s', idx)
