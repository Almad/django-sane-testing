from django.http import HttpResponse

def twohundred(request):
    return HttpResponse(content='200 OK')

