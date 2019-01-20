import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout as __logout__
from django.contrib.auth.decorators import login_required
from django.views import generic as gc
from django.shortcuts import redirect, render
import requests

from . import models as md
from .controllers import deezer_auth, library
from .forms import UploadLibraryForm
from .decorators.views import decorate_cbv, paginated_cbv


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
