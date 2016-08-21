from contextlib import contextmanager

from mezzanine.conf import settings
from cartridge.shop.models import ProductVariation

DOWNLOAD_ONLY_OPTION = False
for option_value, option_name in settings.SHOP_OPTION_TYPE_CHOICES:
    if option_name == 'Downloads':
        DOWNLOAD_ONLY_OPTION = str(option_value)


def is_download_only(skus):
    """ Are all products downloads? """
    if DOWNLOAD_ONLY_OPTION:
        variations = ProductVariation.objects.filter(sku__in=skus)

        params = {'option' + DOWNLOAD_ONLY_OPTION: 'Download Only'}
        download_only_variations = variations.filter(**params)

        if variations.count() == download_only_variations.count():
            return True

    return False


@contextmanager
def session_downloads(request):
    # Schema: {<download.slug>: <acquisition.id>}
    yield request.session.setdefault('cartridge_downloads', {})

    request.session.modified = True
