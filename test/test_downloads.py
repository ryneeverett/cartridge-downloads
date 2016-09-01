import os.path
import shutil
try:
    from unittest import mock
except ImportError:  # python2
    import mock

from django import test
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.core import mail
from django.forms import HiddenInput, NumberInput

from mezzanine.forms.models import Field, Form
from mezzanine.pages.middleware import PageMiddleware
from mezzanine.pages.views import page as mezzanine_page_view
from cartridge.shop.checkout import CHECKOUT_STEP_LAST
from cartridge.shop.models import (
    Cart, Order, OrderItem, Product, ProductOption, ProductVariation)
from cartridge.shop.views import checkout_steps

from bs4 import BeautifulSoup
from django_downloadview.test import temporary_media_root

from cartridge_downloads.admin import DownloadAdmin
from cartridge_downloads.page_processors import (
    override_mezzanine_form_processor)
from cartridge_downloads.models import (
    Acquisition, Download, Purchase, Transaction)
from cartridge_downloads.checkout import order_handler
from cartridge_downloads.views import (
    views, override_cartridge, override_filebrowser)
from cartridge_downloads.utils import credential, session_downloads


class DownloadModelTests(test.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.download = Download.objects.get_or_create(
            file='/path/to/fake/file.ext')[0]

        site = admin.AdminSite()
        download_admin = DownloadAdmin(Download, site)
        request = mock.Mock()
        cls.download_form = download_admin.get_form(request)

        super(DownloadModelTests, cls).setUpClass()

    def test_slug(self):
        """ The slug should be synchronized with the filename. """
        self.assertEqual(self.download.slug, self.download.file.filename)

    def test_change_filename(self):
        """ The filename cannot change because it serves as the slug. """
        form_instance = self.download_form(
            {'file': '/path/to/fake/different.ext'}, instance=self.download)
        self.assertEqual(
            form_instance.errors,
            {'__all__': ['The filename "file.ext" must remain the same.']})

    def test_change_filepath(self):
        """ The file path can change if the filename is the same. """
        form_instance = self.download_form(
            {'file': '/path/to/fake/file.ext'}, instance=self.download)
        self.assertEqual(form_instance.errors, {})

    def test_duplicate_filename(self):
        """ Duplicate filenames are not allowed. """
        form_instance = self.download_form({'file': '/path/to/fake/file.ext'})
        self.assertEqual(
            form_instance.errors,
            {'__all__': ['A download with that file name already exists.']})


class TransactionModelTests(test.TestCase):
    def test_make_credentials(self):
        transaction = Transaction.objects.create()
        credentials = transaction.make_credentials()
        transaction.save()

        lookup_transaction = Transaction.objects.get(id=credentials['id'])

        self.assertEqual(transaction, lookup_transaction)
        self.assertTrue(lookup_transaction.check_token(credentials['token']))

    def test_token(self):
        transaction = Transaction.objects.create()
        token = transaction.make_token()

        self.assertTrue(transaction.check_token(token))
        self.assertFalse(transaction.check_token('not-the-token'))


class OrderHandlerTests(test.TestCase):
    variation_sku = 0

    @classmethod
    def setUpClass(cls):
        option = ProductOption.objects.create(type=1, name='Download Only')
        option.save()

        super(OrderHandlerTests, cls).setUpClass()

    def setUp(self):
        self.order = Order.objects.create()
        self.product = Product.objects.create()

        self.download = Download.objects.create()
        self.download.products.add(self.product)
        self.download.save()

        self.variation = ProductVariation.objects.create(
            sku=self.variation_sku, product=self.product)
        self.variation_sku += 1

        OrderItem.objects.create(order=self.order, sku=self.variation.sku)

        self.request = test.RequestFactory().get('/')
        SessionMiddleware().process_request(self.request)
        self.request.cart = Cart.objects.create()
        self.request.cart.add_item(self.variation, 1)
        self.request.session.save()

    @property
    def product_is_download_purchase(self):
        return Purchase.objects.filter(product=self.product).exists()

    def test_all_digital_download_only(self):
        """
        All products are digital and all variations are download_only.
        """
        self.request.cart.is_download_only = True
        self.variation.option1 = 'Download Only'
        self.variation.save()

        order_handler(self.request, mock.Mock(), self.order)

        self.assertTrue(self.product_is_download_purchase)
        self.assertEqual(self.order.status, 2)

    def test_all_digital_not_download_only(self):
        """
        All products are digital, but the variations aren't all download_only.
        """
        self.request.cart.is_download_only = False
        order_handler(self.request, mock.Mock(), self.order)

        self.assertTrue(self.product_is_download_purchase)
        self.assertEqual(self.order.status, 1)

    def test_not_digital(self):
        """ Non-digital products. """
        self.request.cart.is_download_only = False
        self.product.downloads.clear()
        self.product.save()

        order_handler(self.request, mock.Mock(), self.order)

        self.assertNotIn('cartridge_downloads', self.request.session)
        self.assertFalse(self.product_is_download_purchase)
        self.assertEqual(self.order.status, 1)


class TestOrderConfirmationEmail(test.TestCase):
    def test_cartridge_order(self):
        request = test.RequestFactory().post(
            '/', data={'step': CHECKOUT_STEP_LAST})
        request.user = User.objects.get_or_create(pk=1)[0]

        product = Product.objects.create()
        product.save()

        SessionMiddleware().process_request(request)

        def setup_cart():
            request.cart = Cart.objects.create()
            request.cart.add_item(
                ProductVariation.objects.create(product=product), 1)
            request.cart.is_download_only = False

            request.session['cart'] = request.cart.pk
            request.session.save()

        setup_cart()

        self.assertEqual(len(mail.outbox), 0)

        checkout_steps(request)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Your order has been successful', mail.outbox[0].body)
        self.assertNotIn('access your downloads', mail.outbox[0].body)

        download = Download.objects.create()
        download.products.add(product)
        download.save()

        setup_cart()

        checkout_steps(request)
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('Your order has been successful', mail.outbox[0].body)
        self.assertIn('access your downloads', mail.outbox[1].body)


class TestFormConfirmationEmail(test.TestCase):
    """ HACK Separate classes avoids segmentation fault. """
    def test_mezzanine_form(self):
        page = Form.objects.create(slug='my-form')
        page.save()

        field = Field.objects.create(
            form=page,
            field_type=3,
            required=False)
        field.save()

        page_middleware = PageMiddleware()

        request = test.RequestFactory().post(
            '/my-form', data={'field_1': 'somebody@example.com'})
        request.user = User.objects.get_or_create(pk=1)[0]

        SessionMiddleware().process_request(request)
        request.session.save()

        self.assertEqual(len(mail.outbox), 0,)

        page_middleware.process_view(request, mezzanine_page_view, {}, {})
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn('access your downloads', mail.outbox[0].body)

        download = Download.objects.create()
        download.forms.add(page)
        download.save()

        page_middleware.process_view(request, mezzanine_page_view, {}, {})
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('access your downloads', mail.outbox[1].body)


class OverrideMezzanineFormProcessorTests(test.TestCase):
    def setUp(self):
        # Must post some data or the form will not be bound.
        self.request = test.RequestFactory().post('/', data={'not': 'None'})

        SessionMiddleware().process_request(self.request)
        self.request.session.save()

        self.page = Form.objects.create()
        self.page.save()

    def test_downloads(self):
        download = Download.objects.create(file='test_downloads.ext')
        self.page.downloads.add(download)
        self.page.save()

        response = override_mezzanine_form_processor(self.request, self.page)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/downloads/')

    def test_no_downloads(self):
        response = override_mezzanine_form_processor(self.request, self.page)
        self.assertIsNone(response)
        self.assertNotIn('cartridge_downloads', self.request.session)


class SignalTests(test.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.surviving_product = Product.objects.create()
        cls.surviving_product.save()

        cls.surviving_download = Download.objects.create(slug='survivor')
        cls.surviving_download.products.add(cls.surviving_product)
        cls.surviving_download.save()

        super(SignalTests, cls).setUpClass()

    def setUp(self):
        self.doomed_download = Download.objects.create(slug='doomed')
        self.doomed_download.save()

    def test_purge_downloads_on_delete(self):
        """ When products are deleted, remove downloads with no product. """
        doomed_product = Product.objects.create()
        doomed_product.save()

        self.surviving_download.products.add(doomed_product)
        self.surviving_download.save()

        self.doomed_download.products.add(doomed_product)
        self.doomed_download.save()

        self.assertTrue(Download.objects.filter(slug='doomed').exists())

        doomed_product.delete()
        doomed_product.save()

        self.assertTrue(Download.objects.filter(slug='survivor').exists())
        self.assertFalse(Download.objects.filter(slug='doomed').exists())

    def test_purge_downloads_on_change(self):
        """ When downloads are removed from a ManyToManyField, purge. """
        product = Product.objects.create()
        product.save()

        self.surviving_download.products.add(product)
        self.surviving_download.save()

        self.doomed_download.products.add(product)
        self.doomed_download.save()

        self.assertTrue(Download.objects.filter(slug='doomed').exists())

        product.downloads.remove(self.doomed_download)
        product.save()

        self.assertTrue(Download.objects.filter(slug='survivor').exists())
        self.assertFalse(Download.objects.filter(slug='doomed').exists())


class DownloadViewTests(test.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request = test.RequestFactory().get('/')
        SessionMiddleware().process_request(cls.request)
        cls.request.session.save()
        setattr(cls.request, '_messages', FallbackStorage(cls.request))

        cls.product = Product.objects.create()
        cls.product.save()

        super(DownloadViewTests, cls).setUpClass()

    def _set_up_download_file(self, basename):
        temp_file = os.path.join(settings.MEDIA_ROOT, basename)
        with open(temp_file, 'a'):
            os.utime(temp_file, None)

        download = Download.objects.create(file=temp_file)
        download.products.add(self.product)
        download.save()

        return download

    def _set_up(self):
        """ Run this from within test method to use temporary media root. """
        self.basename = 'download_file.txt'
        self.download = self._set_up_download_file(self.basename)

        order = Order.objects.create()
        order.save()

        transaction = Transaction.objects.create()
        credential(self.request, transaction.make_credentials())
        transaction.save()

        self.purchase = Purchase.objects.create(
            download=self.download,
            transaction=transaction,
            product=self.product,
            order=order)
        self.purchase.save()

        another_download = self._set_up_download_file('another_file.txt')
        another_purchase = Purchase.objects.create(
            download=another_download,
            transaction=transaction,
            product=self.product,
            order=order)
        another_purchase.save()

    @temporary_media_root()
    def test_index(self):
        self._set_up()
        self.request.user = User.objects.get_or_create(pk=1)[0]

        response = views.index(self.request)
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, 'html5lib')
        self.assertEqual(
            len(soup.find_all('a', href='/downloads/download_file.txt')), 1)

    @temporary_media_root()
    def test_download(self):
        self._set_up()

        response = views.download(self.request, slug=self.download.slug)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.attachment)
        self.assertEqual(response.get_basename(), self.basename)

    @temporary_media_root()
    def test_cookie_not_found(self):
        self._set_up()

        with session_downloads(self.request) as session:
            del session['id']
            del session['token']

        with self.assertRaises(PermissionDenied):
            views.download(self.request, slug=self.download.slug)

    @temporary_media_root()
    def test_acquisition_does_not_exist_unauthorized(self):
        """
        The file may exist, but the user is not authorized to access it.
        """
        self._set_up()

        different_file = os.path.join(settings.MEDIA_ROOT, 'different.txt')
        shutil.copy(
            os.path.join(settings.MEDIA_ROOT, self.basename), different_file)

        different_download = Download.objects.create(file=different_file)
        different_download.save()

        with self.assertRaises(Acquisition.DoesNotExist):
            views.download(self.request, slug=different_download.slug)

    @temporary_media_root()
    def test_download_limit(self):
        self._set_up()

        self.purchase.download_count = self.purchase.download_limit
        self.purchase.save()

        response = views.download(self.request, slug=self.download.slug)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(hasattr(response, 'attachment'))

        messages = [m.message for m in get_messages(self.request)]
        self.assertEqual(
            messages,
            ['Download Limit Exceeded. Please contact us for assistance.'])


class OverrideViewTests(test.TestCase):
    @classmethod
    def setUpClass(cls):
        option = ProductOption.objects.create(type=1, name='Download Only')
        option.save()

        cls.product = Product.objects.create(sku=1)
        cls.product.save()

        super(OverrideViewTests, cls).setUpClass()

    def setUp(self):
        self.request = test.RequestFactory().get('/')

    def test_cartridge_product(self):
        self.request.user = User.objects.get_or_create(pk=1)[0]

        response = override_cartridge.product(self.request, self.product.slug)
        product_form = response.context_data['add_product_form']
        # XXX For some reason this cannot fail so it's a worthless test.
        self.assertIsInstance(product_form.base_fields['quantity'].widget,
                              HiddenInput)

    def test_cartridge_cart(self):
        self.request.cart = Cart.objects.create()

        conventional_product_variation = ProductVariation.objects.create(
            product=self.product, sku=3)
        conventional_product_variation.save()

        digital_product_variation = ProductVariation.objects.create(
            product=self.product, sku=4)
        digital_product_variation.option1 = 'Download Only'
        digital_product_variation.save()

        self.request.cart.add_item(conventional_product_variation, 5)
        self.request.cart.add_item(digital_product_variation, 5)

        response = override_cartridge.cart(self.request, 'cart')
        cart_formset = response.context_data['cart_formset']

        conventional_form = cart_formset[0]
        digital_form = cart_formset[1]

        self.assertIsInstance(conventional_form.fields['quantity'].widget,
                              NumberInput)
        self.assertIsInstance(digital_form.fields['quantity'].widget,
                              HiddenInput)
        self.assertEqual(conventional_form.instance.quantity, 5)
        self.assertEqual(digital_form.instance.quantity, 1)

    def test_filebrowser_delete(self):
        download = Download.objects.get_or_create(slug='somefile.txt')[0]

        self.request.user = User.objects.get_or_create(pk=1)[0]
        SessionMiddleware().process_request(self.request)
        self.request.session.save()
        setattr(self.request, '_messages', FallbackStorage(self.request))
        self.request.GET = self.request.GET.copy()
        self.request.GET['filename'] = download.slug

        response = override_filebrowser.delete(self.request)

        self.assertEqual(response.status_code, 302)

        messages = [m.message for m in get_messages(self.request)]
        self.assertEqual(
            messages,
            ["To delete somefile.txt you must delete it's associated product first."])
