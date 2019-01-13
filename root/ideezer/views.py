import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout as __logout__
from django.contrib.auth.decorators import login_required
from django.views import generic as gc
from django.shortcuts import redirect, render

from . import models as md
from .controllers import deezer_auth as d_auth_ctl, library
from .forms import UploadLibraryForm
from .decorators.views import decorate_cbv, paginated_cbv


logger = logging.getLogger(__name__)
SESSION_ATTRIBUTES = ('token', 'expires', 'user_picture_url', 'duser_id')


def deezer_auth(request):
    logger.info('deezer_auth')
    url = d_auth_ctl.build_auth_url(request)
    return redirect(url)


def deezer_redirect(request):
    session = request.session
    try:
        token_info = d_auth_ctl.get_token(request)

        session['token'] = token_info.token
        session['expires'] = token_info.expires

        about_user = d_auth_ctl.about_user(token_info.token)
        session['duser_id'] = about_user.deezer_id
        session['user_picture_url'] = about_user.picture_url

        user = authenticate(
            request, deezer_id=about_user.deezer_id,
            deezer_name=about_user.deezer_name)
        login(request, user)

        msg = 'Deezer auth success. Token expires in {} min {} sec'.format(
            token_info.seconds_left // 60, token_info.seconds_left % 60)
        messages.success(request, msg)
        logger.info('Deezer auth success for %s. Token expires in %s sec',
                    request.user, token_info.seconds_left)
        _redirect = session.pop('redirect', 'main')

        for key in SESSION_ATTRIBUTES:
            if key not in session:
                logger.warning('key %s does not saved to session', key)
    except d_auth_ctl.DeezerAuthException:
        messages.error(request, 'Deezer auth was unsuccessful for {}'.format(
            request.user))
        _redirect = 'main'

    return redirect(_redirect)


def logout(request):
    __logout__(request)

    for key in SESSION_ATTRIBUTES:
        request.session.pop(key, None)

    messages.success(request, 'You have logout.')
    logger.info('logout')
    return redirect('main')


@login_required
def upload_library(request):
    if request.method == 'POST':
        form = UploadLibraryForm(request.POST, request.FILES)
        if form.is_valid():  # TODO custom file validation here?
            library.save(file=request.FILES['file'], user=request.user)
            messages.success(
                request, 'Upload success. Processing make take a few minutes.')
            return redirect('main')
    else:
        form = UploadLibraryForm()

    return render(request, 'ideezer/itunes_xml_upload.html', {'form': form})


class UserFilterViewMixin:
    def get_queryset(self):
        duser_id = self.request.session.get('duser_id')
        return self.model.objects.by_duser(duser_id=duser_id)


@paginated_cbv
class TrackListView(UserFilterViewMixin, gc.ListView):
    template_name = 'ideezer/track_list.html'
    model = md.UserTrack


class TrackDetailView(UserFilterViewMixin, gc.DetailView):
    template_name = 'ideezer/track_detail.html'
    model = md.UserTrack


@paginated_cbv
class PlaylistListView(UserFilterViewMixin, gc.ListView):
    template_name = 'ideezer/playlist_list.html'
    model = md.Playlist


class PlaylistDetailView(UserFilterViewMixin, gc.DetailView):
    template_name = 'ideezer/playlist_detail.html'
    model = md.Playlist


@paginated_cbv(paginate_by=10, paginate_orphans=3)
@decorate_cbv(login_required)
class UploadHistoryListView(UserFilterViewMixin, gc.ListView):
    template_name = 'ideezer/itunes_xml_upload_history.html'
    model = md.UploadHistory
