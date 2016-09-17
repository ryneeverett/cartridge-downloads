from mezzanine.conf import settings
from cartridge.shop.checkout import default_billship_handler
from cartridge.shop.models import Product, ProductVariation
from cartridge.shop.utils import set_shipping

from .models import Purchase, Transaction
from .utils import credential


DOWNLOAD_ONLY_OPTION = False
for option_value, option_name in settings.SHOP_OPTION_TYPE_CHOICES:
    if option_name == 'Downloads':
        DOWNLOAD_ONLY_OPTION = {'option' + str(option_value): 'Download Only'}


def billship_handler(request, order_form):
    """
    If product is all downloads, do not set shipping (defaults to free).
    """
    request.is_download_only  = (
        not ProductVariation.objects
            .filter(sku__in=request.cart.skus())
            .exclude(**DOWNLOAD_ONLY_OPTION)
            .exists()
        if DOWNLOAD_ONLY_OPTION else False)

    if request.is_download_only:
        set_shipping(request, "Free shipping", 0)
    else:
        default_billship_handler(request, order_form)


def order_handler(request, order_form, order):
    skus = request.cart.skus()
    variations = ProductVariation.objects.filter(sku__in=skus)

    download_products = (
        Product.objects
        .filter(variations__in=variations)
        .exclude(downloads=None))

    if download_products.exists():
        # Initialize transaction and credentials.
        transaction = Transaction.objects.create()
        credential(request, transaction.make_credentials())
        transaction.save()

        # Associate downloads with transaction.
        for product in download_products:
            for download in product.downloads.all():
                purchase = Purchase(
                    download=download,
                    transaction=transaction,
                    order=order,
                    product=product)
                purchase.save()

    # If order is all downloads, mark it as processed.
    if (request.is_download_only and
            settings.SHOP_ORDER_STATUS_CHOICES[1] == (2, 'Processed')):
        order.status = 2
        order.save()
