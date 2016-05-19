from django.shortcuts import redirect
from django.template import RequestContext

from mezzanine.forms.forms import FormForForm
from mezzanine.forms.page_processors import form_processor
from mezzanine.forms.models import FormEntry

from .models import Promotion
from .utils import session_downloads


def override_mezzanine_form_processor(request, page):
    """ Override mezzanine.forms.page_processors.form_processor """
    if request.method == 'POST':
        form = FormForForm(page.form, RequestContext(request),
                           request.POST or None, request.FILES or None)
        downloads = page.form.downloads

        if form.is_valid() and downloads.exists():
            form_processor(request, page)

            # HACK: Depends on the form entry created in form_processor having
            # the latest entry_time.
            formentry = (
                FormEntry.objects
                .filter(form=form.form)
                .order_by('entry_time')
                .last())

            promotion = Promotion(formentry=formentry)
            promotion.save()

            with session_downloads(request) as customer_acquisitions:
                for download in downloads.all():
                    customer_acquisitions[download.slug] = promotion.id

            return redirect('downloads_index')
