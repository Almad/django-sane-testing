from django.http import HttpResponse
from testapp.models import ExampleModel

class HttpResponseNotAuthorized(HttpResponse):
    status_code = 401

def twohundred(request):
    return HttpResponse(content='200 OK')

def assert_two_example_models(request):
    assert 2 == len(ExampleModel.objects.all())
    return HttpResponse(content='200 OK')

def return_not_authorized(request):
    return HttpResponseNotAuthorized("401 Not Authorized")
