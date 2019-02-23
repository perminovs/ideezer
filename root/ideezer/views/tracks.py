import logging

from django.contrib.auth.decorators import login_required
from django.views import generic as gc
from django.shortcuts import redirect, get_object_or_404


from .base import UserFilterViewMixin
from .. import models as md
from ..controllers import deezer_search
from ..decorators.views import decorate_cbv, paginated_cbv

logger = logging.getLogger(__name__)


@paginated_cbv
@decorate_cbv(login_required)
class TrackListView(UserFilterViewMixin, gc.ListView):
    template_name = 'ideezer/track_list.html'
    model = md.UserTrack


@decorate_cbv(login_required)
class TrackDetailView(UserFilterViewMixin, gc.DetailView):
    template_name = 'ideezer/track_detail.html'
    model = md.UserTrack


def search_track(request, tid, pid):
    track: md.UserTrack = get_object_or_404(
        md.UserTrack, pk=tid, user=request.user)

    deezer_track = deezer_search.combined(track, one=True)
    if deezer_track:
        ti = md.TrackIdentity.create_or_update(
            user_track=track,
            deezer_track=deezer_track,
        )
        ti.chosen = True
        ti.save()

    return redirect('playlist_detail', pid)
