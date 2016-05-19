import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.shortcuts import redirect, render

from django_downloadview import ObjectDownloadView

from ..models import Acquisition, Download

# https://docs.djangoproject.com/en/stable/topics/logging/#django-request
logger = logging.getLogger('django.request')


def index(request):
    try:
        downloads = request.session['cartridge_downloads']
    except KeyError:
        logger.warning('Cookie not found.', exc_info=True)
        raise PermissionDenied

    acquisition_pages = [
        acq.page for acq in
        Acquisition.objects.filter(id__in=downloads.values())
        .select_subclasses()
    ]

    return render(request,
                  'shop/downloads/index.html',
                  {'acquisition_pages': acquisition_pages})


class CartridgeDownloadView(ObjectDownloadView):
    def get(self, request, slug):
        # Look up purchase.
        try:
            purchase_id = request.session['cartridge_downloads'][slug]
        except KeyError:
            logger.warning(
                'Cookie not found or slug not found in session.',
                exc_info=True)
            raise PermissionDenied

        acquisition = Acquisition.objects.get_subclass(id=purchase_id)

        if acquisition.download_count >= acquisition.download_limit:
            # Do nothing if the download limit has been reached.
            messages.add_message(
                request,
                messages.ERROR,
                'Download Limit Exceeded. Please contact us for assistance.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            # Proceed with download.
            acquisition.download_count = F('download_count') + 1
            acquisition.save()

            return super(CartridgeDownloadView, self).get(self, request, slug)

download = CartridgeDownloadView.as_view(model=Download)
