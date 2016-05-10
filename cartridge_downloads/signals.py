from django.db.models.signals import pre_delete
from django.dispatch import receiver

from cartridge.shop.models import Product


@receiver(pre_delete, sender=Product)
def clean_downloads(sender, **kwargs):
    """ When a product is deleted, delete dangling related downloads. """
    for download in kwargs['instance'].downloads.all():
        if download.products.count() == 1:
            download.delete()
