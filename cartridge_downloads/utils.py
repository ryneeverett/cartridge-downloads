import contextlib
try:
    from urllib.parse import urlencode
except ImportError:  # python2
    from urllib import urlencode

try:
    from django.urls import reverse
except ImportError:  # django<1.10
    from django.core.urlresolvers import reverse


@contextlib.contextmanager
def session_downloads(request):
    # Schema: {id: <id>, token: <token>}
    yield request.session.setdefault('cartridge_downloads', {})

    request.session.modified = True


def credential(request, credentials):
    with session_downloads(request) as session:
        session.update(credentials)

    # Pass credentials in url parameters for email template context.
    from .views.views import index
    request.download_url = '{scheme}://{host}{url}?{querystring}'.format(
        scheme=request.scheme,
        host=request.get_host(),
        url=reverse(index),
        querystring=urlencode(credentials))
