from django.contrib import messages
from django.contrib.auth import login as __login__, logout as __logout__
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views import generic as gc
from django.shortcuts import redirect

from . import models as md
from .controllers import deezer_auth as d_auth_ctl
from .controllers import logger


class AuthFormView(gc.FormView):
    form_class = AuthenticationForm
    template_name = 'ideezer/auth_form.html'

    success_url = '/'

    def form_valid(self, form):
        __login__(self.request, form.get_user())
        messages.success(self.request, 'You have login.')

        # FIXME `next` param from @login_required does not work
        prev = self.request.META.get('HTTP_REFERER', None)
        if prev and '?next=' in prev:
            # 'http://localhost:8083/ideezer/auth?next=/ideezer/deezer_auth' ->
            # -> '/ideezer/deezer_auth'
            self.success_url = prev[prev.rfind('?next=') + 6:]
            logger.info(
                '`success_url` changed to {}'.format(self.success_url),
                self.request,
            )
        return super(AuthFormView, self).form_valid(form)


def logout(request):
    __logout__(request)
    messages.success(request, 'You have logout.')
    logger.info('logout', request)
    return redirect('main')


@login_required
def deezer_auth(request):
    logger.info('deezer_auth', request)
    url = d_auth_ctl.build_auth_url(request)
    return redirect(url)


@login_required
def deezer_redirect(request):
    try:
        token, expires_time, seconds_left = d_auth_ctl.get_token(request)
        request.session['token'] = token
        request.session['expires'] = expires_time
        msg = 'Deezer auth success. Token expires in {} min {} sec'.format(
            seconds_left // 60, seconds_left % 60)
        messages.success(request, msg)
        logger.info(
            'Deezer auth success for {}. Token expires in {} sec'.format(
                request.user, seconds_left),
            request)
        _redirect = request.session.pop('redirect', 'main')
    except d_auth_ctl.DeezerAuthException:
        messages.error(request, 'Deezer auth was unsuccessful for {}'.format(
            request.user))
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
