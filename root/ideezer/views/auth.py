import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout as __logout__
from django.shortcuts import redirect
import requests

from ..controllers import deezer_auth

logger = logging.getLogger(__name__)


def deezer_auth_view(request):
    logger.info('deezer_auth')
    url = deezer_auth.build_auth_url(request)
    return redirect(url)


def deezer_redirect(request):
    redirect_path = 'main'
    session = request.session

    try:
        token_info = deezer_auth.get_token(request)
        user_info = deezer_auth.about_user(token_info.token)
    except deezer_auth.DeezerAuthRejected:
        messages.warning(request, 'Deezer auth was rejected')
        return redirect(redirect_path)
    except deezer_auth.DeezerUnexpectedResponse:
        messages.error(
            request, 'Unexpected Deezer behaviour, auth was unsuccessful')
        return redirect(redirect_path)
    except requests.HTTPError:
        logger.exception('deezer auth error')
        messages.error(request, 'Deezer auth was unsuccessful')
        return redirect(redirect_path)

    user = authenticate(
        request, deezer_id=user_info.deezer_id,
        deezer_name=user_info.deezer_name)
    login(request, user)
    deezer_auth.update_session(session, token_info, user_info)

    msg = 'Deezer auth success. Token expires in {} min {} sec'.format(
        token_info.seconds_left // 60, token_info.seconds_left % 60)
    messages.success(request, msg)
    logger.info('Deezer auth success for %s. Token expires in %s sec',
                request.user, token_info.seconds_left)

    redirect_path = session.pop('redirect', redirect_path)
    return redirect(redirect_path)


def logout(request):
    __logout__(request)
    deezer_auth.clear_session(request.session)

    messages.success(request, 'You have logout.')
    return redirect('main')
