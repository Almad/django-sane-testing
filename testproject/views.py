from django.http import HttpResponse, HttpResponseServerError
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

def return_server_error(request):
    return HttpResponseServerError("500 Server error")

def return_django_error(request):
    raise Exception('500 Django error')
