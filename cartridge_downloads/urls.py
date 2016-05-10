from django.conf.urls import url

from .views import views

urlpatterns = [
    url('^$', views.index, name='downloads_index'),
    url('^(?P<slug>.+)', views.download, name='downloads_download'),
]
