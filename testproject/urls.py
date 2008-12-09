from django.conf.urls.defaults import *

from views import twohundred

urlpatterns = patterns('',
    (r'^testtwohundred/$', twohundred),
)
