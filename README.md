Digital product support for the [Django](https://github.com/django/django)/[Mezzanine](https://github.com/stephenmcd/mezzanine)/[Cartridge](https://github.com/stephenmcd/cartridge) stack, with support for large files with [django_downloadview](https://github.com/benoitbryon/django-downloadview).

**THIS IS ALPHAWARE. I RESERVE THE RIGHT TO NUKE THE MIGRATIONS BEFORE THE INITIAL RELEASE.**

# Features

- Adds download fields to the `Product` admin, which are available upon order completion.
- Adds download fields to the `Form` admin, which are available upon form completion.

## Download Only Variations *(optional)*

Often times a download is bundled with a physical product -- mp3's may come with a cd or an epub might come with a book. In this case it often makes sense to have one variation for just the download and another for the physical good *and* the download.

### Product Page
- When all variations of a product are "download only", it's quantity field is hidden.

### Cart Page

- The quantity field of "download only" variations is forced to "1" and hidden.

### Orders

When orders consist solely of "download only" products, they get:

  - marked as processed automatically
  - free shipping

To enable this feature:

1. Add a "Download" type to the setting `SHOP_OPTION_TYPE_CHOICES`.
2. Add a `ProductOption` named "Download Only" to the "Download" type.

# Installation

```sh
# This special invocation is to get my branch of filebrowser-safe which I
# believe will eventually be merged into upstream. It will cause some
# "DEPRECATION" noise, but the replacement functionality hasn't been built into
# pip yet, so we'll have to put up with it.
pip install -e git+https://github.com/ryneeverett/cartridge-downloads.git#egg=cartridge-downloads --process-dependency-links

python manage.py migrate
```

## settings.py

```py
# OPTIONALLY, if you're using the "download only" feature and want free shipping for transactions consisting of only those products.
SHOP_HANDLER_BILLING_SHIPPING = "cartridge_downloads.checkout.billship_handler"

# Alternately, you could call this handler method from your own handler.
SHOP_HANDLER_ORDER = 'cartridge_downloads.checkout.order_handler'
...
# OPTIONALLY, specify allowed file formats here. Defaults to allowing all.
FILEBROWSER_SELECT_FORMATS = {
    ...
    'Download': ['Document'],
}
...
INSTALLED_APPS = (
...
    'cartridge_downloads',  # Before cartridge.shop
    ...
    'cartridge.shop',
    ...
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

# How it works

There's quite a bit more going on than this, but it's mostly UI hacks. Here's a summary of the mechanics:

1. Monkey patch an inline to our `Download` model onto cartridge/mezzanine's `ProductAdmin`/`FormAdmin`.
2. When a user successfully submits an order/form, create an `Acquisition` referencing the `Download`s, add a reference to it to their session, and direct them to the `/downloads/` view.
3. The `/downloads/` view looks at the `Acquisitions` in the user's session and only links to `Download`s they have acquired.

# Development

```sh
cd cartridge-downloads
pip install -e . --process-dependency-links -c constraints.txt
python test
```
