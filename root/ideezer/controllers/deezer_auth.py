from datetime import datetime, timedelta
import requests
from django.conf import settings

__dt_format = '%Y.%m.%d %H:%M:%S'


class DeezerAuthException(Exception):
    def __init__(self, error, error_reason):
        self.error = error
        self.error_reason = error_reason


def build_auth_uri(redirect_uri):
    """ Returns url to login user on deezer.com
    """
    return (
        'https://connect.deezer.com/oauth/auth.php?app_id={app_id}&'
        'redirect_uri={redirect_uri}&perms={perms}'.format(
            app_id=settings.DEEZER_APP_ID,
            redirect_uri=redirect_uri,
            perms=settings.DEEZER_BASE_PERMS,
        )
    )


def get_token(GET):
    """ Run after application authorized and get `token` and its `expires_time`
    """
    code = GET.get('code', None)
    if not code:
        raise DeezerAuthException(
            error=GET.get('error', None),
            error_reason=GET.get('error_reason', None)
        )

    url = 'https://connect.deezer.com/oauth/access_token.php?'
    params = {
        'app_id': settings.DEEZER_APP_ID, 'secret': settings.DEEZER_SECRET_KEY,
        'code': code
    }
    resp = requests.post(url, params)
    resp_text = resp.text
    resp_text = resp_text.replace('access_token=', '')
    idx = resp_text.rfind('&expires=')
    token = resp_text[:idx]
    expires = resp_text[idx + len('&expires='):]
    expires_time = datetime.now() + timedelta(seconds=int(expires))

    return token, expires_time.strftime(__dt_format)
