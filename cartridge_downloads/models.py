import uuid

from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.crypto import get_random_string

from mezzanine.conf import settings
from mezzanine.core.fields import FileField

from model_utils.managers import InheritanceManager


class Download(models.Model):
    file = FileField(upload_to='downloads', format=(
        'Download' if 'Download' in settings.FILEBROWSER_SELECT_FORMATS
        else ''))

    products = models.ManyToManyField('shop.Product', related_name='downloads')
    forms = models.ManyToManyField('forms.Form', related_name='downloads')

    slug = models.SlugField(unique=True, editable=False)

    def __str__(self):
        return self.slug

    def clean(self):
        # On modification, do not allow filename to change.
        if self.slug and self.slug != self.file.filename:
            raise ValidationError(
                'The filename "{f}" must remain the same.'.format(f=self.slug))

    def save(self, *args, **kwargs):
        # On initial save, set slug to filename.
        self.slug = self.file.filename if not self.slug else self.slug
        super(Download, self).save(*args, **kwargs)

    def validate_unique(self, *args, **kwargs):
        # Do not allow duplicate filenames.
        try:
            download = Download.objects.get(slug=self.file.filename)
        except Download.DoesNotExist:
            pass
        else:
            # We're ok if we're changing the file but the filename is the same.
            if download != self:
                raise ValidationError(
                    'A download with that file name already exists.')

        super(Download, self).validate_unique(*args, **kwargs)


class Transaction(models.Model):
    # Use a uuid because these get exposed to users and we don't necessarily
    # want to reveal the transaction count to them.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    token_hash = models.CharField(max_length=128)

    def make_credentials(self):
        return {'id': self.id, 'token': self.make_token()}

    def make_token(self):
        token = get_random_string()

        # We don't need a real salt because the attacks salts protect against
        # aren't applicable to random "passwords".
        self.token_hash = make_password(token, salt='fake_salt')

        return token

    def check_token(self, token):
        return check_password(token, self.token_hash)


class Acquisition(models.Model):
    download = models.ForeignKey('Download', on_delete=models.PROTECT)
    download_count = models.IntegerField(default=0,
                                         editable=False,
                                         verbose_name='Download Count')
    download_limit = models.IntegerField(default=5,
                                         verbose_name='Download Limit')
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT)

    objects = InheritanceManager()

    @property
    def page(self):
        """
        Return a related model which must have 'title' and 'downloads' fields.
        """
        raise NotImplementedError


class Purchase(Acquisition):
    order = models.ForeignKey(
        'shop.Order', on_delete=models.PROTECT, editable=False)
    product = models.ForeignKey(
        'shop.Product', on_delete=models.PROTECT, editable=False)

    @property
    def page(self):
        return self.product


class Promotion(Acquisition):
    formentry = models.ForeignKey(
        'forms.FormEntry', on_delete=models.PROTECT, editable=False)

    @property
    def page(self):
        return self.formentry.form
