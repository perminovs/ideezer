import logging
from tempfile import NamedTemporaryFile
from plistlib import InvalidFileException

from django.conf import settings
from libpytunes import Library, Playlist

from ..celery_app import celery_app
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


def save(file, user, async_mode=True):
    with NamedTemporaryFile(dir=settings.UPLOAD_PATH, delete=False) as tmp:
        for chunk in file.chunks():
            tmp.write(chunk)

    if not async_mode:
        process(path=tmp.name, user_id=user.id)
        return

    celery_app.send_task('process_itunes_library', kwargs={
        'path': tmp.name, 'user_id': user.id,
    })


@celery_app.task(name='process_itunes_library', bind=True)
def process(self, path, user_id):
    logger.info('process file: %s for user %s', path, user_id)
    history = md.UploadHistory.start(task_id=self.request.id, user_id=user_id)

    try:
        lib = Library(itunesxml=path)
    except InvalidFileException as ife:
        history.mark_failed(error=f'process error: {ife}')
        logger.warning('process error: %s', ife)
        return

    try:
        # TODO merge playlist?
        playlist_deleted, track_delete = clear_user_itunes_data(user_id)
        insert_tracks(lib, user_id)
        playlists_created = insert_playlists(lib, user_id)
    except Exception as e:  # TODO -> by celery signals
        history.mark_failed(error=str(e))
        raise

    history.mark_success(
        playlists_deleted=playlist_deleted,
        tracks_deleted=track_delete,
        playlists_created=playlists_created,
        tracks_created=len(lib.songs.values()),
    )


@timeit
def clear_user_itunes_data(user_id):
    _, pl_info = md.Playlist.objects.by_user(user_id).delete()
    _, tr_info = md.UserTrack.objects.by_user(user_id).delete()
    return pl_info['ideezer.Playlist'], tr_info['ideezer.UserTrack']


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

    created_cnt = 0
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
        created_cnt += 1

        if idx % 10 == 0:
            logger.info('iter: %s', idx)
    return created_cnt
