import sys

from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from cartridge.shop.models import Product, ProductVariation

import splinter

from cartridge_downloads.models import Download

import testbase

DEBUG = '--debug' in sys.argv

drivers = ['phantomjs', 'firefox', 'chrome']
try:
    WEBDRIVER = set(drivers).intersection(sys.argv).pop()
except KeyError:
    WEBDRIVER = 'phantomjs'


class TestBrowser(StaticLiveServerTestCase, testbase.DownloadTestMixin):
    @classmethod
    def setUpClass(cls):
        kwargs = {}

        if WEBDRIVER == 'phantomjs':
            # XXX Might add '--remote-debugger-port=9000' but throws exception.
            kwargs['service_args'] = [
                '--webdriver-loglevel=DEBUG'] if DEBUG else []

        try:
            cls.browser = splinter.Browser(WEBDRIVER, **kwargs)
        except splinter.exceptions.DriverNotFoundError:
            cls.browser = splinter.Browser('firefox')

        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()

    @classmethod
    def visit_relativeurl(cls, relativeurl):
        cls.browser.visit(cls.live_server_url + relativeurl)

    def test_download_purchase(self):
        product = Product.objects.create(available=True)
        product.save()

        download = Download.objects.create(file='/tmp/fakefile.ext')
        download.products.add(product)
        download.save()

        variation = ProductVariation.objects.create(
            sku=self.variation_sku, product=product, unit_price=1.0)
        variation.save()

        self.visit_relativeurl(product.get_absolute_url())
        self.browser.find_by_value('Buy').click()

        self.browser.find_link_by_partial_text('Go to Checkout').click()

        self.browser.fill_form({
            'billing_detail_first_name': 'Sam',
            'billing_detail_last_name': 'Clemens',
            'billing_detail_street': '123 Sarcasm Ln',
            'billing_detail_city': 'Hartford',
            'billing_detail_state': 'Connecticut',
            'billing_detail_postcode': 12345,
            'billing_detail_country': 'United States',
            'billing_detail_phone': '5555555',
            'billing_detail_email': 'mark@example.com',
        })
        self.browser.find_by_value('Next').click()

        self.browser.fill_form({
            'card_name': 'SAMUEL CLEMENS',
            'card_number': 4242424242424242,
            'card_ccv': 000,
        })
        self.browser.choose('card_type', 'Visa')
        self.browser.find_by_value('Next').click()

        self.browser.find_by_value('Next').click()

        self.browser.find_by_text(
            'Download your digital products here.').click()

        self.assertTrue(self.browser.is_text_present('fakefile.ext'))
