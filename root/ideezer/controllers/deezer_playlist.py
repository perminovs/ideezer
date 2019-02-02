import logging

from .deezer_base import request
from .. import models as md

# https://developers.deezer.com/api/playlist

logger = logging.getLogger(__name__)


CREATE_URL = 'https://api.deezer.com/user/me/playlists'
ADDTRACKS_URL = 'https://api.deezer.com/playlist/{playlist_id}/tracks'
INFO_URL = 'https://api.deezer.com/playlist/{playlist_id}'


def create(playlist: md.Playlist, token):
    deezer_data = request(
        method='post', url=CREATE_URL,
        params={'title': playlist.itunes_title, 'access_token': token},
    )
    playlist.deezer_id = deezer_data['id']
    playlist.deezer_title = playlist.itunes_title
    playlist.save()
    logger.debug('%s created', playlist)
    return deezer_data


def add_tracks(playlist: md.Playlist, token):
    deezer_track_ids = tuple(
        identity.deezer_track.deezer_id
        for identity in playlist.identities
    )
    deezer_track_ids_csv = ','.join(map(str, deezer_track_ids))
    deezer_data = request(
        method='post', url=ADDTRACKS_URL.format(playlist_id=playlist.deezer_id),
        params={'songs': deezer_track_ids_csv, 'access_token': token},
    )
    logger.debug('%s: %s tracks added', playlist, len(deezer_track_ids))
    return deezer_data


def info(playlist: md.Playlist, token):
    return request(
        url=INFO_URL.format(playlist_id=playlist.deezer_id),
        params={'access_token': token},
    )
