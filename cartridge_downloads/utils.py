from contextlib import contextmanager

from mezzanine.conf import settings
from cartridge.shop.models import ProductVariation


def is_download_only(skus):
    """ Are all products downloads? """
    for option_index, option_name in settings.SHOP_OPTION_TYPE_CHOICES:
        if option_name == 'Downloads':
            variations = ProductVariation.objects.filter(sku__in=skus)

            params = {'option' + str(option_index): 'Download Only'}
            download_only_variations = variations.filter(**params)

            if variations.count() == download_only_variations.count():
                return True
            else:
                break

    return False


@contextmanager
def session_downloads(request):
    # Schema: {<download.slug>: <acquisition.id>}
    yield request.session.setdefault('cartridge_downloads', {})

    request.session.modified = True
