from django.contrib import messages
from django.shortcuts import redirect

from filebrowser_safe import views

from ..models import Download


def delete(request):
    filename = request.GET.get('filename', '')

    if filename:
        try:
            Download.objects.get(slug=filename)
        except Download.DoesNotExist:
            pass
        else:
            messages.add_message(
                request,
                messages.ERROR,
                "To delete {f} you must delete it's associated product first."
                .format(f=filename))
            return redirect(request.META.get('HTTP_REFERER', '/'))

    return views.delete(request)
