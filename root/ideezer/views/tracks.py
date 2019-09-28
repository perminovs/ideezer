import logging

from django.contrib.auth.decorators import login_required
from django.views import generic as gc
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.edit import UpdateView

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
class UserTrackEdit(UpdateView):
    model = md.UserTrack
    fields = ['_s_title', '_s_artist', '_s_album']
    template_name_suffix = '_update_form'

    def get_context_data(self, **kwargs):
        context = super(UserTrackEdit, self).get_context_data(**kwargs)
        track: md.UserTrack = context['object']
        context['identities'] = []

        # TODO paginate
        identities = md.TrackIdentity.objects.filter(user_track=track).all()
        for identity in identities:
            if identity.chosen:
                context['chosen_deezer_track'] = identity
            else:
                context['identities'].append(identity)
        return context


def set_track_identity(request, track_id, identity_id):
    user_track = get_object_or_404(md.UserTrack, pk=track_id)
    exists = md.TrackIdentity.objects.filter(  # TODO убрать отсюда
        user_track=user_track,
        chosen=True,
    ).first()
    if exists:
        exists.chosen = False
        exists.save()

    identity = get_object_or_404(md.TrackIdentity, pk=identity_id)
    identity.chosen = True
    identity.save()
    return redirect('track_edit', track_id)


def search_track_from_playlist(request, tid, pid):
    _search_track(request, tid, mark_best=True)
    return redirect('playlist_detail', pid)


def search_track_from_track(request, tid):
    _search_track(request, tid, mark_best=True)
    return redirect('track_edit', tid)


def _search_track(request, tid: int, mark_best: bool):  # TODO убрать отсюда
    track: md.UserTrack = get_object_or_404(
        md.UserTrack, pk=tid, user=request.user)

    deezer_track = deezer_search.combined(track, one=True)
    if deezer_track:
        ti = md.TrackIdentity.create_or_update(
            user_track=track,
            deezer_track=deezer_track,
        )
        ti.set_diff()

        if mark_best:
            exists: md.TrackIdentity = md.TrackIdentity.objects.filter(
                user_track=track, chosen=True
            ).first()
            if not exists:
                ti.chosen = True
                ti.set_diff()
                ti.save()
            elif exists.id == ti.id:
                pass
            elif exists.chosen and exists.diff < ti.diff:
                pass
            else:
                exists.chosen = False
                exists.save()
                ti.chosen = True
                ti.set_diff()
                ti.save()

    return deezer_track
