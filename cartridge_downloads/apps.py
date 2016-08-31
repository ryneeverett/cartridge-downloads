import logging

from django.apps import AppConfig

from mezzanine.conf import settings


class DownloadsConfig(AppConfig):
    name = 'cartridge_downloads'

    def ready(self):
        # Register signals.
        from . import signals

        # When registering by decorator, the last app in INSTALLED_APPS gets
        # called first. But in order to override cartridge templates, we need to
        # be before cartridge in INSTALLED_APPS. Therefore we register here
        # after all apps have been init'd.
        from mezzanine.forms.models import Form
        from mezzanine.pages.page_processors import processor_for
        from .page_processors import override_mezzanine_form_processor
        processor_for(Form)(override_mezzanine_form_processor)

        if not settings.SESSION_COOKIE_SECURE:
            logger = logging.getLogger(__name__)
            logger.warning(
                'SESSION_COOKIE_SECURE is not set! Cartridge-Downloads stores '
                'client credentials in session cookies.')
