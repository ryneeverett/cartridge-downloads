from django.shortcuts import redirect
from django.template import RequestContext

from mezzanine.forms.forms import FormForForm
from mezzanine.forms.models import FormEntry
from mezzanine.forms.page_processors import form_processor

from .models import Promotion
from .utils import transact


def process_promotion(request, page):
    """
    The meat of the form processor, pulled out for ease of customization.
    """
    # Initialize transaction and credentials. This must run before mezzanine's
    # form processor in order for the credentials to be included in the email.
    transaction = transact(request)

    # Call mezzanine's form_processor.
    form_processor(request, page)

    # HACK: Depends on the form entry created in form_processor having
    # the latest entry_time.
    formentry = (
        FormEntry.objects
        .filter(form=page.form)
        .order_by('entry_time')
        .last())

    # Associate downloads with transaction.
    for download in page.form.downloads.all():
        promotion = Promotion(
            download=download,
            transaction=transaction,
            formentry=formentry)
        promotion.save()

    return redirect('downloads_index')


def override_mezzanine_form_processor(request, page):
    """ Override mezzanine.forms.page_processors.form_processor """
    if request.method == 'POST':
        form = FormForForm(page.form, RequestContext(request),
                           request.POST or None, request.FILES or None)

        if form.is_valid() and page.form.downloads.exists():
            return process_promotion(request, page)
