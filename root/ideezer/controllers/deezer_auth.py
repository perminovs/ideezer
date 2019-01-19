import logging
from datetime import datetime, timedelta
from typing import NamedTuple, Tuple

import requests
from django.conf import settings

logger = logging.getLogger(__name__)
__dt_format = '%Y.%m.%d %H:%M:%S'


class TokenInfo(NamedTuple):
    token: str
    expires: str
    seconds_left: int


class AboutUser(NamedTuple):
    deezer_id: int
    deezer_name: str
    picture_url: str


class DeezerAuthRejected(Exception):
    pass


class DeezerUnexpectedResponse(Exception):
    pass


def build_auth_url(request):
    """ Returns url to login user on deezer.com
    """
    redirect_uri = request.build_absolute_uri('deezer_redirect')
    url = __build_auth_url(redirect_uri, request)
    return url


def __build_auth_url(redirect_uri, request):
    redirect_uri = redirect_uri.replace('127.0.0.1', 'localhost')  # FIXME

    # браузер должен получить url типа `http://hostname/...`
    # вместо `http://web/...`
    # где `hostname` - реальный домен машины, например, locahost
    # (этот запрос придёт в nginx);
    # `web` - имя сервиса, по которому nginx проксирует запрос в gunicorn
    if settings.HOSTNAME:
        _src_uri = redirect_uri
        http_host = request.META.get('HTTP_HOST')
        redirect_uri = redirect_uri.replace(
            'http://{service}/'.format(service=http_host),
            'http://{host}/'.format(host=settings.HOSTNAME),
        )
        logger.info('redirect_uri was changed from: `%s` to `%s`',
                    _src_uri, redirect_uri)

    return (
        'https://connect.deezer.com/oauth/auth.php?app_id={app_id}&'
        'redirect_uri={redirect_uri}&perms={perms}'.format(
            app_id=settings.DEEZER_APP_ID,
            redirect_uri=redirect_uri,
            perms=settings.DEEZER_BASE_PERMS,
        )
    )


def get_token(request) -> TokenInfo:
    """ Run after application authorized and get `token` and its `expires_time`
    """
    code = request.GET.get('code', None)
    if not code:
        logger.warning('auth rejected')
        raise DeezerAuthRejected('auth rejected')

    url = 'https://connect.deezer.com/oauth/access_token.php?'
    params = {
        'app_id': settings.DEEZER_APP_ID, 'secret': settings.DEEZER_SECRET_KEY,
        'code': code
    }
    resp = requests.post(url, params)
    resp.raise_for_status()

    token, seconds_left = __parse_deezer_response(resp)
    expires_time = datetime.now() + timedelta(seconds=seconds_left)

    return TokenInfo(
        token=token,
        expires=expires_time.strftime(__dt_format),
        seconds_left=seconds_left,
    )


def __parse_deezer_response(response: requests.Response) -> Tuple[str, int]:
    resp_text = response.text
    resp_text = resp_text.replace('access_token=', '')
    idx = resp_text.rfind('&expires=')
    token = resp_text[:idx]
    seconds_left = int(resp_text[idx + len('&expires='):])
    return token, seconds_left


def about_user(token) -> AboutUser:
    url = 'https://api.deezer.com/user/me'
    resp = requests.get(url, {'access_token': token})
    resp.raise_for_status()

    info = resp.json()
    error = info.get('error')
    deezer_id = info.get('id')
    deezer_name = info.get('name')
    if not error and (not deezer_id or not deezer_name):
        error = (f'unexpected deezer response format: '
                 f'id: "{deezer_id}", name: "{deezer_name}"')
    if error:
        logger.error('auth error: %s', error)
        raise DeezerUnexpectedResponse(error)

    return AboutUser(
        deezer_id=deezer_id,
        deezer_name=deezer_name,
        picture_url=info.get('picture_small'),
    )
