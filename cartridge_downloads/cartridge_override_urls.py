from django.conf.urls import url

from mezzanine.conf import settings

from .views import override_cartridge

_slash = "/" if settings.APPEND_SLASH else ""

urlpatterns = [
    url("^product/(?P<slug>.*)%s$" % _slash,
        override_cartridge.product,
        name="shop_product"),
    url("^cart%s$" % _slash, override_cartridge.cart, name="shop_cart"),
]
