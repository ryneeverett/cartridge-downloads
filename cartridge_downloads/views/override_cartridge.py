""" Wrappers around cartridge views to hide quantity. """
import copy

from django.forms import HiddenInput
from django.shortcuts import get_object_or_404

from cartridge.shop import views as cartridge_views
from cartridge.shop.forms import AddProductForm, CartItemFormSet
from cartridge.shop.models import Product, ProductVariation

from ..checkout import DOWNLOAD_ONLY_OPTION


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
        products_are_download_only = (
            [ProductVariation.objects.filter(
                sku__in=[sku], **DOWNLOAD_ONLY_OPTION).exists()
             for sku in skus] if DOWNLOAD_ONLY_OPTION else [])
        download_only_product_indexes = [
            i for i, b in enumerate(products_are_download_only) if b]

        for i in download_only_product_indexes:
            # Set quantity to 1.
            cart_formset[i].instance.quantity = 1
            cart_formset[i].instance.save()

            # Hide quantity field.
            cart_formset[i].fields['quantity'].widget = HiddenInput()

    return cartridge_views.cart(request, **kwargs)
