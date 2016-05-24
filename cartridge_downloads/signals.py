from django.db.models.signals import post_delete
from django.dispatch import receiver

from cartridge.shop.models import Product

from .models import Download


@receiver(post_delete, sender=Product)
def purge_downloads(sender, **kwargs):
    """ When a product is deleted, delete dangling downloads. """
    Download.objects.filter(products=None).delete()
