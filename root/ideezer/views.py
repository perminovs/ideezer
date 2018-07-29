from django.contrib.auth import login, logout as __logout__
from django.contrib.auth.forms import AuthenticationForm
from django.views import generic as gc
from django.shortcuts import redirect

from . import models as md


class AuthFormView(gc.FormView):
    form_class = AuthenticationForm
    template_name = 'ideezer/auth_form.html'

    success_url = '/ideezer/'

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super(AuthFormView, self).form_valid(form)


def logout(request):
    __logout__(request)
    return redirect('main')


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
