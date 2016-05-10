from django import template

from cartridge.shop.models import Product

register = template.Library()


@register.filter
def is_download(items):
    """ Is any one of the items a digital product? """
    skus = [item.sku for item in items]
    return (Product.objects
            .filter(variations__sku__in=skus)
            .exclude(downloads__isnull=True)
            .exists())


@register.filter
def download_slugs(download_queryset):
    return download_queryset.values_list('slug', flat=True)
