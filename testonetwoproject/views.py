from django.http import HttpResponse
from testapp.models import ExampleModel

def twohundred(request):
    return HttpResponse(content='200 OK')
