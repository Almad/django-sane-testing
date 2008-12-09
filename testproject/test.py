import urllib2

from django.test import TestCase

from djangosanetesting.cases import HttpTestCase

class TestUnit(TestCase):
    def test_empty(self):
        pass

class TestLiveServerRunning(HttpTestCase):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        # I did not found how to load those variables from django.conf.settings,
        # so I must just hardcode them. Advices welcomed.
        self.host = 'localhost'
        self.port = 8000
    
    def test_server_retrievable(self):
        self.assertEquals(u'200 OK', urllib2.urlopen('http://%(host)s:%(port)s/testtwohundred/' % {
            'host' : self.host,
            'port' : self.port
        }).read())

