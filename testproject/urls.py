from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    (r'^testtwohundred/$', twohundred),
    (r'^assert_two_example_models/$', assert_two_example_models),
    (r'^return_not_authorized/$', return_not_authorized),
)
