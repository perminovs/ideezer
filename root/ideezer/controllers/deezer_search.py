import requests

from .. import models as md

# https://developers.deezer.com/api/search

URL = 'https://api.deezer.com/search'
LIMIT = 100


class DeezerResponseError(Exception):  # TODO move to especial module
    def __init__(self, type_, message, code):
        super(DeezerResponseError, self).__init__()
        self.type = type_
        self.message = message
        self.code = code

    def __str__(self):
        return f'{self.type}: {self.message} ({self.message})'


def simple(track: md.UserTrack, with_album=True, token=None, limit=None):
    query = f'{track.s_artist} - {track.s_title}'
    if with_album and track.s_album:
        query = f'{query} {track.s_album}'
    return _search(query, token, limit)


def advanced(track: md.UserTrack, with_album=True, token=None, limit=None):
    query = f'artist:"{track.s_artist}" track:"{track.s_title}"'
    if with_album and track.s_album:
        query = f'{query} album:"{track.s_album}"'
    return _search(query, token, limit)


def _search(query, token=None, limit=None):
    limit = limit or LIMIT
    params = {'q': query, 'limit': limit}
    if token:
        params['access_token'] = token

    deezer_data = _request(URL, params)
    return tuple(
        md.DeezerTrack.from_deezer(track_info)
        for track_info in deezer_data
    )


def _request(url, params):
    response = requests.get(url, params=params)
    response.raise_for_status()
    json = response.json()

    error = json.get('error')
    if error:
        raise DeezerResponseError(
            type_=error.get('type'),
            message=error.get('message'),
            code=error.get('code'),
        )

    return json['data'] if 'data' in json else json