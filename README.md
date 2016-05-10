Digital product support for the [Django](https://github.com/django/django)/[Mezzanine](https://github.com/stephenmcd/mezzanine)/[Cartridge](https://github.com/stephenmcd/cartridge) stack, with support for large files with [django_downloadview](https://github.com/benoitbryon/django-downloadview).

**THIS IS ALPHAWARE. I RESERVE THE RIGHT TO NUKE THE MIGRATIONS BEFORE THE INITIAL RELEASE.**

# Installation

```sh
# This special invocation is to get my branch of filebrowser-safe which I
# believe will eventually be merged into upstream. It will cause some
# "DEPRECATION" noise, but the replacement functionality hasn't been built into
# pip yet, so we'll have to put up with it.
pip install -e git+https://github.com/ryneeverett/cartridge-downloads.git@downloads#egg=filebrowser_safe-999 --process-dependency-links

python manage.py migrate
```

## settings.py

```py
# Alternately, you could call this handler method from your own handler.
SHOP_HANDLER_ORDER = 'cartridge_downloads.order.handler'
...
# OPTIONALLY, specify allowed file formats here. Defaults to allowing all.
FILEBROWSER_SELECT_FORMATS = {
    ...
    'Download': ['Document'],
}
...
INSTALLED_APPS = (
...
    'cartridge_downloads',  # Before cartridge.shop.
    ...
    'cartridge.shop',
...
)
```

## urls.py

```py
from cartridge_downloads.views import override_filebrowser
...
urlpatterns = [
...
    # Cartridge-Downloads' URLs (before cartridge urls).
    url("^downloads/", include('cartridge_downloads.urls')),
    url("^shop/(?=(product|cart))",
        include('cartridge_downloads.cartridge_override_urls')),
    url(r'^delete/$', override_filebrowser.delete, name="fb_delete"),
...
]
```

# Development

```sh
cd cartridge-downloads
python setup.py develop
python test
```
