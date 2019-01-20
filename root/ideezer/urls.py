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

from . import views

urlpatterns = [
    path(r'logout', views.logout, name='logout'),
    path(r'deezer_auth', views.deezer_auth_view, name='deezer_auth'),
    path(r'deezer_redirect', views.deezer_redirect, name='deezer_redirect'),
    path(r'upload_library', views.upload_library, name='upload_library'),
    path(r'upload_history', views.UploadHistoryListView.as_view(), name='upload_history'),
    path(r'tracks', views.TrackListView.as_view(), name='track_list'),
    path(r'track/<int:pk>', views.TrackDetailView.as_view(), name='track_detail'),
    path(r'playlists', views.PlaylistListView.as_view(), name='playlist_list'),
    path(r'playlist/<int:pk>', views.PlaylistDetailView.as_view(), name='playlist_detail'),
    path(r'license', TemplateView.as_view(template_name='ideezer/license.html'), name='license'),
    path(r'', TemplateView.as_view(template_name='ideezer/main.html'), name='main'),
    path(r'vtest', views.vtest, name='vtest'),
]
