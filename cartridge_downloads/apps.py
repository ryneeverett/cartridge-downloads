from django.apps import AppConfig


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
