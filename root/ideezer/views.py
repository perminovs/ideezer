import logging

from django.contrib import messages
from django.views import generic as gc
from django.shortcuts import redirect

from . import models as md
from .controllers import deezer_auth as d_auth_ctl


logger = logging.getLogger(__name__)


def deezer_auth(request):
    logger.info('deezer_auth')
    url = d_auth_ctl.build_auth_url(request)
    return redirect(url)


def deezer_redirect(request):
    session = request.session
    try:
        token, expires_time, seconds_left = d_auth_ctl.get_token(request)
        session['token'] = token
        session['expires'] = expires_time

        deezer_id = d_auth_ctl.about_user(token)
        session['duser_id'] = deezer_id
        md.User.objects.get_or_create(deezer_id=deezer_id)

        msg = 'Deezer auth success. Token expires in {} min {} sec'.format(
            seconds_left // 60, seconds_left % 60)
        messages.success(request, msg)
        logger.info(
            'Deezer auth success for {}. Token expires in {} sec'.format(
                request.user, seconds_left
            ))
        _redirect = session.pop('redirect', 'main')
    except d_auth_ctl.DeezerAuthException:
        messages.error(request, 'Deezer auth was unsuccessful for {}'.format(
            request.user))
        _redirect = 'main'

    return redirect(_redirect)


class UserFilterViewMixin:
    def get_queryset(self):
        user_id = self.request.session.get('duser_id')
        return self.model.objects.by_user(user_id=user_id)


class TrackListView(UserFilterViewMixin, gc.ListView):
    template_name = 'ideezer/track_list.html'
    model = md.UserTrack


class TrackDetailView(UserFilterViewMixin, gc.DetailView):
    template_name = 'ideezer/track_detail.html'
    model = md.UserTrack


class PlaylistListView(UserFilterViewMixin, gc.ListView):
    template_name = 'ideezer/playlist_list.html'
    model = md.Playlist


class PlaylistDetailView(UserFilterViewMixin, gc.DetailView):
    template_name = 'ideezer/playlist_detail.html'
    model = md.Playlist
