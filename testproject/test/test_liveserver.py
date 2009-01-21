import urllib2
from djangosanetesting.cases import HttpTestCase, SeleniumTestCase

class TestLiveServerRunning(HttpTestCase):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        # I did not found how to load those variables from django.conf.settings,
        # so I must just hardcode them. Advices welcomed.
        self.host = 'localhost'
        self.port = 8000
    
    def get_ok(self):
        self.assertEquals(u'200 OK', urllib2.urlopen('http://%(host)s:%(port)s/testtwohundred/' % {
            'host' : self.host,
            'port' : self.port
        }).read())
    
    def test_http_retrievable(self):
        return self.get_ok()
    
    def test_http_retrievable_repeatedly(self):
        return self.get_ok()


class TestSeleniumWorks(SeleniumTestCase):
    def test_ok(self):
        self.selenium.open("/testtwohundred/")
        self.selenium.is_text_present("200 OK")
