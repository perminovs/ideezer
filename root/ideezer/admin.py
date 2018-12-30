from django.contrib import admin
from . import models as md

admin.site.register(md.UserTrack)
admin.site.register(md.DeezerTrack)
admin.site.register(md.Playlist)
admin.site.register(md.TrackIdentity)
admin.site.register(md.User)
