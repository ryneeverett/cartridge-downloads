import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.shortcuts import redirect, render

from cartridge.shop.models import Product

from django_downloadview import ObjectDownloadView

from ..models import Purchase, Download

# https://docs.djangoproject.com/en/stable/topics/logging/#django-request
logger = logging.getLogger('django.request')


def index(request):
    try:
        downloads = request.session['cartridge_downloads']
    except KeyError:
        logger.warning('Cookie not found.', exc_info=True)
        raise PermissionDenied

    digital_products = Product.objects.filter(
        purchase__id__in=downloads.values())
    return render(request,
                  'shop/downloads/index.html',
                  {'digital_products': digital_products})


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

        purchase = Purchase.objects.get(id=purchase_id)

        if purchase.download_count >= purchase.download_limit:
            # Do nothing if the download limit has been reached.
            messages.add_message(
                request,
                messages.ERROR,
                'Download Limit Exceeded. Please contact us for assistance.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            # Proceed with download.
            purchase.download_count = F('download_count') + 1
            purchase.save()

            return super(CartridgeDownloadView, self).get(self, request, slug)

download = CartridgeDownloadView.as_view(model=Download)
