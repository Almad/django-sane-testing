# -*- coding: utf-8 -*-
import urllib2
from djangosanetesting.cases import HttpTestCase, SeleniumTestCase

from testapp.models import ExampleModel

class TestLiveServerRunning(HttpTestCase):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        # I did not found how to load those variables from django.conf.settings,
        # so I must just hardcode them. Advices welcomed.
        self.host = 'localhost'
        self.port = 8000
    
    def get_ok(self):
        try:
            self.assertEquals(u'200 OK', urllib2.urlopen('http://%(host)s:%(port)s/testtwohundred/' % {
                'host' : self.host,
                'port' : self.port
            }).read())
        except urllib2.HTTPError, err:
            if err.fp:
                print err.fp.read()
            raise
    
    def test_http_retrievable(self):
        return self.get_ok()
    
    def test_http_retrievable_repeatedly(self):
        return self.get_ok()
    
    def test_client_available(self):
        res = self.client.get('/testtwohundred/')
        self.assert_equals(200, res.status_code)
    
    def test_not_authorized_not_resetable(self):
        # This is lame, but condition is non-deterministic and reveals itself
        # when repeating request often...
        for i in xrange(1, 10):
            try:
                response = urllib2.urlopen(url='http://%(host)s:%(port)s/return_not_authorized/' % {
                    'host' : self.host,
                    'port' : self.port
                },
                data='data')
                #response = opener.open(request)
            except urllib2.HTTPError, err:
                self.assert_equals(401, err.code)
            else:
                assert False, "401 expected"

class TestSeleniumWorks(SeleniumTestCase):
    def setUp(self):
        super(TestSeleniumWorks, self).setUp()
#        from django.utils import translation
#        translation.activate("cs")

    def test_ok(self):
        self.selenium.open("/testtwohundred/")
        self.selenium.is_text_present("200 OK")

    def test_czech_string_acquired_even_with_selenium(self):
        self.assert_equals(u"Přeložitelný řetězec", unicode(ExampleModel.get_translated_string()))
