from django.contrib import admin
from django.core import urlresolvers
from django.utils import safestring

from cartridge.shop.admin import ProductAdmin, OrderAdmin
from mezzanine.forms.admin import FormAdmin

from .models import Download, Purchase


class DownloadAdmin(admin.ModelAdmin):
    model = Download
    fields = ('file',)

    def in_menu(self):
        return False


class PurchaseAdmin(admin.ModelAdmin):
    model = Purchase

    def in_menu(self):
        return False


class ProductDownloadInline(admin.TabularInline):
    model = Download.products.through
    verbose_name_plural = 'Downloads'


class FormDownloadInline(admin.TabularInline):
    model = Download.forms.through
    verbose_name_plural = 'Promotional Downloads'


class PurchaseInline(admin.TabularInline):
    model = Purchase
    verbose_name_plural = 'Download Purchases'
    readonly_fields = ('product_link', 'download_count')
    fields = ('product_link', 'download_count', 'download_limit')
    extra = 0

    def product_link(self, obj):
        change_view_url = urlresolvers.reverse(
            'admin:shop_product_change', args=(obj.product.id,))
        return safestring.mark_safe(
            '<a href="{}">{}</a>'.format(change_view_url, obj.product))

    product_link.short_description = 'Product'


admin.site.register(Download, DownloadAdmin)
admin.site.register(Purchase, PurchaseAdmin)
ProductAdmin.inlines += (ProductDownloadInline,)
FormAdmin.inlines += (FormDownloadInline,)
OrderAdmin.inlines += (PurchaseInline,)
