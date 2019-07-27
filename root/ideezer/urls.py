"""ideezer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from django.views.generic import TemplateView

from .views import auth, library, tracks, playlists

urlpatterns = [
    path(r'logout', auth.logout, name='logout'),
    path(r'deezer_auth', auth.deezer_auth_view, name='deezer_auth'),
    path(r'deezer_redirect', auth.deezer_redirect, name='deezer_redirect'),
    path(r'upload_library', library.upload_library, name='upload_library'),
    path(r'upload_history', library.UploadHistoryListView.as_view(), name='upload_history'),
    path(r'tracks', tracks.TrackListView.as_view(), name='track_list'),
    path(r'track/<int:pk>', tracks.TrackDetailView.as_view(), name='track_detail'),
    path(r'search_track/<int:tid>/<int:pid>', tracks.search_track, name='search_track'),
    path(r'playlists', playlists.PlaylistListView.as_view(), name='playlist_list'),
    path(r'playlist/<int:pk>', playlists.PlaylistDetailView.as_view(), name='playlist_detail'),
    path(r'license', TemplateView.as_view(template_name='ideezer/license.html'), name='license'),
    path(r'playlist_search_simple/<int:pk>', playlists.playlist_search_simple, name='playlist_search_simple'),
    path(r'playlist_deezer_create/<int:pk>', playlists.playlist_deezer_create, name='playlist_deezer_create'),
    path(r'playlist_link_choose/<int:pk>', playlists.playlist_link_choose, name='playlist_link_choose'),
    path(r'identity_clear/<int:pk>/<int:playlist_from>', playlists.identity_clear, name='identity_clear'),
    path(r'', TemplateView.as_view(template_name='ideezer/main.html'), name='main'),
]
