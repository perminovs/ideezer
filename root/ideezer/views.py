from django.contrib import messages
from django.contrib.auth import login as __login__, logout as __logout__
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views import generic as gc
from django.shortcuts import redirect

import logging

from . import models as md
from .controllers import deezer_auth as d_auth_ctl


logger = logging.getLogger(__name__)


class AuthFormView(gc.FormView):
    # FIXME `next` param from @login_required does not work
    form_class = AuthenticationForm
    template_name = 'ideezer/auth_form.html'

    success_url = '/ideezer/'

    def form_valid(self, form):
        __login__(self.request, form.get_user())
        messages.success(self.request, 'You have login.')
        return super(AuthFormView, self).form_valid(form)


def logout(request):
    __logout__(request)
    messages.success(request, 'You have logout.')
    return redirect('main')


@login_required
def deezer_auth(request):
    url = d_auth_ctl.build_auth_url(request)
    return redirect(url)


@login_required
def deezer_redirect(request):
    try:
        token, expires_time = d_auth_ctl.get_token(request.GET)
        request.session['token'] = token
        request.session['expires'] = expires_time
        messages.success(request, 'Deezer auth success')
        logger.info('auth success for {}'.format(request.user))
        _redirect = request.session.pop('redirect', 'main')
    except d_auth_ctl.DeezerAuthException:
        messages.error(request, 'Deezer auth was unsuccessful')
        _redirect = 'main'

    return redirect(_redirect)


class UserFilterViewMixin:
    def get_queryset(self):
        return self.model.by_user(user=self.request.user)


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
