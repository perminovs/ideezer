import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound
from django.views import generic as gc
from django.shortcuts import redirect, get_object_or_404, render

from .base import UserFilterViewMixin
from .. import models as md
from ..controllers import deezer_playlist, deezer_search
from ..decorators.views import decorate_cbv, paginated_cbv


logger = logging.getLogger(__name__)


@paginated_cbv
class PlaylistListView(UserFilterViewMixin, gc.ListView):
    template_name = 'ideezer/playlist_list.html'
    model = md.Playlist


@decorate_cbv(login_required)
class PlaylistDetailView(UserFilterViewMixin, gc.DetailView):
    template_name = 'ideezer/playlist_detail.html'
    model = md.Playlist
    obj = None

    def get_object(self, queryset=None):
        self.obj = super(PlaylistDetailView, self).get_object(queryset)
        return self.obj

    def get_context_data(self, **kwargs):
        context = super(PlaylistDetailView, self).get_context_data(**kwargs)

        context['paired'] = self.obj.identities
        context['unpaired'] = self.obj.unpaired
        return context


@login_required
def playlist_search_simple(request, pk):
    playlist: md.Playlist = get_object_or_404(
        md.Playlist, pk=pk, user=request.user,
    )

    identities = []
    for track in playlist.itunes_content.all():
        if md.TrackIdentity.mark_exists_track_as_pair(user_track=track):
            continue

        deezer_track = deezer_search.simple(track, one=True)
        if not deezer_track:
            continue
        ti = md.TrackIdentity(
            user_track=track, deezer_track=deezer_track,
            chosen=True,
        )
        ti.set_diff()
        identities.append(ti)
    md.TrackIdentity.objects.bulk_create(identities)

    return redirect('playlist_detail', pk)


@login_required
def playlist_deezer_create(request, pk):
    playlist: md.Playlist = get_object_or_404(
        md.Playlist, pk=pk, user=request.user,
    )
    token = request.session.get('token')
    deezer_playlist.create(playlist=playlist, token=token)
    deezer_playlist.add_tracks(playlist=playlist, token=token)
    playlist_info = deezer_playlist.info(playlist=playlist, token=token)

    deezer_url = playlist_info.get('link')
    if deezer_url:
        return redirect(deezer_url)
    logger.warning('unexpected response: `%s` - missed link', playlist_info)
    return redirect('playlist_detail', pk)


@login_required
def identity_clear(request, pk, playlist_from):
    identity: md.TrackIdentity = get_object_or_404(md.TrackIdentity, pk=pk)
    if identity.user_track.user != request.user:
        return HttpResponseNotFound('Identity does not found')

    identity.delete()

    return redirect('playlist_detail', playlist_from)


@login_required
def playlist_link_choose(request, pk):
    playlist = get_object_or_404(md.Playlist, pk=pk)
    token = request.session.get('token')
    deezer_playlists = deezer_playlist.get_all(token=token)
    context = {'object': playlist, 'deezer_playlists': [1, 2, 3]}
    return render(request, 'ideezer/playlist_link_choose.html', context)
