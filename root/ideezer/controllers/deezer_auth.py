from datetime import datetime, timedelta
import requests
from django.conf import settings

from . import logger

__dt_format = '%Y.%m.%d %H:%M:%S'


class DeezerAuthException(Exception):
    def __init__(self, error, error_reason, url=None):
        self.error = error
        self.error_reason = error_reason
        self.url = url

    def __str__(self):
        url = ', url: {}'.format(self.url) if self.url else ''
        return 'error: "{}", error_reason: "{}"{}'.format(
            self.error, self.error_reason, url
        )


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
        http_host = request.META.get('HTTP_HOST')
        logger.info('source redirect_uri: {}'.format(redirect_uri), None)
        redirect_uri = redirect_uri.replace(
            'http://{service}/'.format(service=http_host),
            'http://{host}/'.format(host=settings.HOSTNAME),
        )
        logger.info('fixed redirect_uri: {}'.format(redirect_uri), None)

    return (
        'https://connect.deezer.com/oauth/auth.php?app_id={app_id}&'
        'redirect_uri={redirect_uri}&perms={perms}'.format(
            app_id=settings.DEEZER_APP_ID,
            redirect_uri=redirect_uri,
            perms=settings.DEEZER_BASE_PERMS,
        )
    )


def get_token(request):
    """ Run after application authorized and get `token` and its `expires_time`
    """
    code = request.GET.get('code', None)
    if not code:
        logger.warning('auth rejected', request)
        raise DeezerAuthException(
            error=request.GET.get('error', None),
            error_reason=request.GET.get('error_reason', None)
        )

    url = 'https://connect.deezer.com/oauth/access_token.php?'
    params = {
        'app_id': settings.DEEZER_APP_ID, 'secret': settings.DEEZER_SECRET_KEY,
        'code': code
    }
    resp = requests.post(url, params)
    if not resp.ok:
        logger.error('response is not ok', request)
        logger.error('resp.status_code: {}, resp.reason: {}'.format(
            resp.status_code, resp.reason),
            request)
        raise DeezerAuthException(
            error=resp.status_code, error_reason=resp.reason, url=url
        )
    resp_text = resp.text
    resp_text = resp_text.replace('access_token=', '')
    idx = resp_text.rfind('&expires=')
    token = resp_text[:idx]
    seconds_left = int(resp_text[idx + len('&expires='):])
    expires_time = datetime.now() + timedelta(seconds=seconds_left)

    return token, expires_time.strftime(__dt_format), seconds_left
