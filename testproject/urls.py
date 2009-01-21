from django.conf.urls.defaults import *

from views import twohundred, assert_two_example_models

urlpatterns = patterns('',
    (r'^testtwohundred/$', twohundred),
    (r'^assert_two_example_models/$', assert_two_example_models),
)
