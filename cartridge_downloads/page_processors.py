from django.shortcuts import redirect
from django.template import RequestContext

from mezzanine.forms.forms import FormForForm
from mezzanine.forms.page_processors import form_processor
from mezzanine.forms.models import FormEntry

from .models import Promotion, Transaction
from .utils import credential


def override_mezzanine_form_processor(request, page):
    """ Override mezzanine.forms.page_processors.form_processor """
    if request.method == 'POST':
        form = FormForForm(page.form, RequestContext(request),
                           request.POST or None, request.FILES or None)
        downloads = page.form.downloads

        if form.is_valid() and downloads.exists():
            # Initialize transaction and credentials.
            transaction = Transaction.objects.create()
            credential(request, transaction.make_credentials())
            transaction.save()

            # Call mezzanine's form_processor.
            form_processor(request, page)

            # HACK: Depends on the form entry created in form_processor having
            # the latest entry_time.
            formentry = (
                FormEntry.objects
                .filter(form=form.form)
                .order_by('entry_time')
                .last())

            # Associate downloads with transaction.
            for download in downloads.all():
                promotion = Promotion(
                    download=download,
                    transaction=transaction,
                    formentry=formentry)
                promotion.save()

            return redirect('downloads_index')
