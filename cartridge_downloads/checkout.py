from mezzanine.conf import settings
from cartridge.shop.models import Product, ProductOption, ProductVariation

from .models import Purchase
from .utils import session_downloads


def order_handler(request, form, order):
    skus = order.items.values_list('sku', flat=True)
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

    # If order is all digital, mark it as processed. (Optional Feature)
    if ProductOption.objects.filter(name='Download Only').exists():
        option = ProductOption.objects.get(name='Download Only')
        params = {'option' + str(option.type): 'Download Only'}
        download_only_variations = variations.filter(**params)

        if (variations.count() == download_only_variations.count() and
                settings.SHOP_ORDER_STATUS_CHOICES[1] == (2, 'Processed')):
            order.status = 2
            order.save()
