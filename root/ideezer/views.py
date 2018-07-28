from django.contrib.auth import login, logout as __logout__
from django.contrib.auth.forms import AuthenticationForm
from django.views import generic as gc
from django.shortcuts import render, redirect

from . import models as md


def main_page(request):
    return render(request, 'ideezer/main.html')


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


class TrackListView(gc.ListView):
    template_name = 'ideezer/track_list.html'
    model = md.UserTrack


class PlaylistListView(gc.ListView):
    template_name = 'ideezer/playlist_list.html'
    model = md.Playlist

