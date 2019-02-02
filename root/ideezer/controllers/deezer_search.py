import logging

from .deezer_base import request
from .. import models as md

# https://developers.deezer.com/api/search

SEARCH_URL = 'https://api.deezer.com/search'
LIMIT = 100

logger = logging.getLogger(__name__)


def simple(
    track: md.UserTrack, with_album=True, token=None,
    limit=None, one=False
):
    query = f'{track.s_artist} - {track.s_title}'
    if with_album and track.s_album:
        query = f'{query} {track.s_album}'
    return _search(query, token, limit, one)


def advanced(
    track: md.UserTrack, with_album=True, token=None,
    limit=None, one=False
):
    query = f'artist:"{track.s_artist}" track:"{track.s_title}"'
    if with_album and track.s_album:
        query = f'{query} album:"{track.s_album}"'
    return _search(query, token, limit, one)


def _search(query, token=None, limit=None, one=False):
    limit = limit or LIMIT
    params = {'q': query, 'limit': limit}
    if token:
        params['access_token'] = token

    deezer_data = request(SEARCH_URL, params)
    logger.debug("deezer response on '%s' with %s tracks", query, len(deezer_data))
    if one:
        if not deezer_data:
            return None
        return md.DeezerTrack.from_deezer(deezer_data[0])

    return tuple(
        md.DeezerTrack.from_deezer(track_info)
        for track_info in deezer_data
    )
