from contextlib import contextmanager


@contextmanager
def session_downloads(request):
    # Schema: {<download.slug>: <acquisition.id>}
    yield request.session.setdefault('cartridge_downloads', {})

    request.session.modified = True
