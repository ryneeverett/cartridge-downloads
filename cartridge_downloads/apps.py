from django.apps import AppConfig


class DownloadsConfig(AppConfig):
    name = 'cartridge_downloads'

    def ready(self):
        # Register signals.
        from . import signals
