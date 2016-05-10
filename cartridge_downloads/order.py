from mezzanine.conf import settings
from cartridge.shop.models import Product

from .models import Purchase


def handler(request, form, order):
    # Schema: {<download.slug>: <purchase.id>}
    customer_purchases = request.session.setdefault('cartridge_downloads', {})

    skus = order.items.values_list('sku', flat=True)
    products = Product.objects.filter(variations__sku__in=skus)
    digital_products = products.exclude(downloads__isnull=True)

    # Create purchase instances and store primary key in the session.
    for product in digital_products:
        purchase = Purchase(order=order, product=product)
        purchase.save()

        for download in product.downloads.all():
            customer_purchases[download.slug] = purchase.id

    # If order is all digital, mark it as processed.
    if (products.count() == digital_products.count() and
            settings.SHOP_ORDER_STATUS_CHOICES[1] == (2, 'Processed')):
        order.status = 2
        order.save()
