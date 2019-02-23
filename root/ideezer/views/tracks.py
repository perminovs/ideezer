from django.contrib.auth.decorators import login_required
from django.views import generic as gc

from .base import UserFilterViewMixin
from .. import models as md
from ..decorators.views import decorate_cbv, paginated_cbv


@paginated_cbv
@decorate_cbv(login_required)
class TrackListView(UserFilterViewMixin, gc.ListView):
    template_name = 'ideezer/track_list.html'
    model = md.UserTrack


@decorate_cbv(login_required)
class TrackDetailView(UserFilterViewMixin, gc.DetailView):
    template_name = 'ideezer/track_detail.html'
    model = md.UserTrack
