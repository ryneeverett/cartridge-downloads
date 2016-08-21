""" Wrappers around cartridge views to hide quantity. """
import copy

from django.forms import HiddenInput
from django.shortcuts import get_object_or_404

from mezzanine.conf import settings

from cartridge.shop import views as cartridge_views
from cartridge.shop.forms import AddProductForm, CartItemFormSet
from cartridge.shop.models import Product, ProductVariation


DOWNLOAD_ONLY_OPTION = False
for option_value, option_name in settings.SHOP_OPTION_TYPE_CHOICES:
    if option_name == 'Downloads':
        DOWNLOAD_ONLY_OPTION = {'option' + str(option_value): 'Download Only'}


def product(request, slug, **kwargs):
    if request.method == 'GET':
        published_products = Product.objects.published(for_user=request.user)
        product = get_object_or_404(published_products, slug=slug)

        # If all product variations are "Download Only":
        if DOWNLOAD_ONLY_OPTION and (
                product.variations.count() ==
                product.variations.filter(**DOWNLOAD_ONLY_OPTION).count()):
            # Copy form_class to avoid modifying the class itself.
            kwargs['form_class'] = copy.deepcopy(
                kwargs.get('form_class', AddProductForm))
            # Hide quantity field.
            kwargs['form_class'].base_fields['quantity'].widget = HiddenInput()

    return cartridge_views.product(request, slug, **kwargs)


def cart(request, slug, **kwargs):
    if request.method == 'GET':
        cart_formset_class = kwargs.setdefault(
            'cart_formset_class', CartItemFormSet)
        cart_formset = cart_formset_class(instance=request.cart)

        # Override cartridge formset.
        extra_context = kwargs.setdefault('extra_context', {})
        extra_context['cart_formset'] = cart_formset

        # Figure out the indexes of the "download only" products.
        skus = [form.instance.sku for form in cart_formset]
        products_are_downloads = (
            [ProductVariation.objects.filter(
                sku__in=[sku], **DOWNLOAD_ONLY_OPTION).exists()
             for sku in skus] if DOWNLOAD_ONLY_OPTION else [])
        download_product_indexes = [
            i for i, b in enumerate(products_are_downloads) if b]

        # Cache is_download_only.
        request.cart.is_download_only = bool(
            len(skus) == len(products_are_downloads))

        for i in download_product_indexes:
            # Set quantity to 1.
            cart_formset[i].instance.quantity = 1
            cart_formset[i].instance.save()

            # Hide quantity field.
            cart_formset[i].fields['quantity'].widget = HiddenInput()

    return cartridge_views.cart(request, **kwargs)
