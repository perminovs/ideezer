import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views import generic as gc

from .base import UserFilterViewMixin
from .. import models as md
from ..controllers import library
from ..forms import UploadLibraryForm
from ..decorators.views import paginated_cbv, decorate_cbv


logger = logging.getLogger(__name__)


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


@paginated_cbv(paginate_by=10, paginate_orphans=3)
@decorate_cbv(login_required)
class UploadHistoryListView(UserFilterViewMixin, gc.ListView):
    template_name = 'ideezer/itunes_xml_upload_history.html'
    model = md.UploadHistory
