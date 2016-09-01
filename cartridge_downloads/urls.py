from django.conf.urls import url

from .views import views

urlpatterns = [
    url('^$', views.index, name='downloads_index'),
    url('^authenticate/(?P<id>.+)/(?P<token>.+)$',
        views.authenticate, name='downloads_authenticate'),
    url('^(?P<slug>.+)', views.download, name='downloads_download'),
]
