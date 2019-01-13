import logging
from typing import Tuple
from tempfile import NamedTemporaryFile

from django.conf import settings
from celery import states
from celery.signals import task_success, task_prerun
from libpytunes import Library, Playlist

from ..celery_app import celery_app
from .. import models as md


logger = logging.getLogger(__name__)
PROCESS_ITUNES_LIBRARY = 'process_itunes_library'


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

    celery_app.send_task(PROCESS_ITUNES_LIBRARY, kwargs={
        'path': tmp.name, 'user_id': user.id,
    })


@task_prerun.connect
def library_upload_prerun_handler(task_id, task, *args, **kwargs):
    if task.name != PROCESS_ITUNES_LIBRARY:
        return

    task.update_state(state=states.STARTED)
    task_kwargs = kwargs['kwargs']
    md.UploadHistory.create(task_id=task_id, user_id=task_kwargs['user_id'])


@task_success.connect
def library_upload_success_handler(result, sender, **kwargs):
    if sender.name != PROCESS_ITUNES_LIBRARY:
        return

    history = md.UploadHistory.objects.get(task__task_id=sender.request.id)
    history.update_info(
        playlists_deleted=result['playlists_deleted'],
        tracks_deleted=result['tracks_deleted'],
        playlists_created=result['playlists_created'],
        tracks_created=result['tracks_created'],
    )


@celery_app.task(name=PROCESS_ITUNES_LIBRARY)
def process(path, user_id) -> dict:
    logger.info('process file: %s for user %s', path, user_id)

    # no need for try-except because
    # on any Exception celery task will be marked as failed
    lib = Library(itunesxml=path)
    playlist_deleted, track_delete = clear_user_itunes_data(user_id)
    insert_tracks(lib, user_id)
    playlists_created = insert_playlists(lib, user_id)

    return dict(
        playlists_deleted=playlist_deleted,
        tracks_deleted=track_delete,
        playlists_created=playlists_created,
        tracks_created=len(lib.songs.values()),
    )


@timeit
def clear_user_itunes_data(user_id) -> Tuple[int, int]:
    _, pl_info = md.Playlist.objects.by_user(user_id).delete()
    _, tr_info = md.UserTrack.objects.by_user(user_id).delete()
    return (
        pl_info.get('ideezer.Playlist', 0),
        tr_info.get('ideezer.UserTrack', 0),
    )


@timeit
def insert_tracks(lib, user_id):
    tracks = (
        md.UserTrack.from_itunes(track, user_id)
        for track in lib.songs.values()
    )
    md.UserTrack.objects.bulk_create(tracks)


@timeit
def insert_playlists(lib, user_id) -> int:
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
