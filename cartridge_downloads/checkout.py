from mezzanine.conf import settings
from cartridge.shop.checkout import default_billship_handler
from cartridge.shop.models import Product, ProductVariation
from cartridge.shop.utils import set_shipping

from .models import Purchase
from .utils import is_download_only, session_downloads


def billship_handler(request, order_form):
    """
    If product is all downloads, do not set shipping (defaults to free).
    """
    if is_download_only(request.cart.skus()):
        set_shipping(request, "Free shipping", 0)
    else:
        default_billship_handler(request, order_form)


def order_handler(request, form, order):
    skus = request.cart.skus()
    variations = ProductVariation.objects.filter(sku__in=skus)

    # Create purchase instances and store primary key in the session.
    download_products = (
        Product.objects
        .filter(variations__in=variations)
        .exclude(downloads=None))

    with session_downloads(request) as customer_acquisitions:
        for product in download_products:
            purchase = Purchase(order=order, product=product)
            purchase.save()

            for download in product.downloads.all():
                customer_acquisitions[download.slug] = purchase.id

    # If order is all digital, mark it as processed.
    if (is_download_only(skus) and
            settings.SHOP_ORDER_STATUS_CHOICES[1] == (2, 'Processed')):
        order.status = 2
        order.save()
