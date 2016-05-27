from django.db.models.signals import m2m_changed, post_delete
from django.dispatch import receiver

from cartridge.shop.models import Product
from mezzanine.forms.models import Form

from .models import Download


def purge_downloads():
    """ Delete dangling downloads. """
    Download.objects.filter(products=None, forms=None).delete()


@receiver(post_delete, sender=Form)
@receiver(post_delete, sender=Product)
def purge_downloads_on_delete(sender, **kwargs):
    purge_downloads()


@receiver(m2m_changed, sender=Form.downloads.through)
@receiver(m2m_changed, sender=Product.downloads.through)
def purge_downloads_on_change(sender, **kwargs):
    if kwargs['action'] == 'post_remove':
        purge_downloads()
