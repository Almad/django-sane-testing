# -*- coding: utf-8 -*-
import urllib2
from djangosanetesting.cases import HttpTestCase, SeleniumTestCase
from djangosanetesting.utils import get_live_server_path

from testapp.models import ExampleModel

class TestLiveServerRunning(HttpTestCase):
    def __init__(self, *args, **kwargs):
        super(TestLiveServerRunning, self).__init__(*args, **kwargs)
        # I did not found how to load those variables from django.conf.settings,
        # so I must just hardcode them. Advices welcomed.
        self.host = 'localhost'
        self.port = 8000
    
    def get_ok(self):
        self.assertEquals(u'200 OK', self.urlopen('http://%(host)s:%(port)s/testtwohundred/' % {
            'host' : self.host,
            'port' : self.port
        }).read())

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
                response = self.urlopen(url='http://%(host)s:%(port)s/return_not_authorized/' % {
                    'host' : self.host,
                    'port' : self.port
                },
                data='data')
                #response = opener.open(request)
            except urllib2.HTTPError, err:
                self.assert_equals(401, err.code)
            else:
                assert False, "401 expected"

    def test_server_error(self):
        try:
            self.urlopen(url='http://%(host)s:%(port)s/return_server_error/' % {
                    'host' : self.host,
                    'port' : self.port
                })
        except urllib2.HTTPError, err:
            self.assert_equals(500, err.code)
            self.assert_equals("500 Server error, traceback not found", err.msg)
            return True
        assert False, "500 expected"

    def test_django_error_traceback(self):
        try:
            self.urlopen(url='http://%(host)s:%(port)s/return_django_error/' % {
                    'host' : self.host,
                    'port' : self.port
                })
        except urllib2.HTTPError, err:
            self.assert_equals(500, err.code)
            self.assert_not_equals("500 Server error, traceback not found", err.msg)
            return True
        assert False, "500 expected"

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

    def test_selenium_server_error(self):
        try:
            self.selenium.open('/return_django_error/')
        except urllib2.HTTPError, err:
            self.assert_equals(500, err.code)
            self.assert_not_equals("500 Server error, traceback not found", err.msg)
            return True
        assert False, "500 expected"

    def test_selenium_django_error_traceback(self):
        try:
            self.selenium.open('/return_server_error/')
        except urllib2.HTTPError, err:
            self.assert_equals(500, err.code)
            self.assert_equals("500 Server error, traceback not found", err.msg)
            return True
        assert False, "500 expected"


class TestTwill(HttpTestCase):

    def test_ok_retrieved(self):
        self.twill.go("%stesttwohundred/" % get_live_server_path())
        self.assert_equals(200, self.twill.get_code())

    def test_live_server_added_when_missing(self):
        self.twill.go("/testtwohundred/")
        self.assert_equals(200, self.twill.get_code())

    def test_missing_recognized(self):
        self.twill.go("/this/should/never/exist/")
        self.assert_equals(404, self.twill.get_code())

    def test_twill_server_error(self):
        try:
            self.twill.go('/return_django_error/')
        except urllib2.HTTPError, err:
            self.assert_equals(500, err.code)
            self.assert_not_equals("500 Server error, traceback not found", err.msg)
            return True
        assert False, "500 expected"

    def test_twill_django_error_traceback(self):
        try:
            self.twill.go('/return_server_error/')
        except urllib2.HTTPError, err:
            self.assert_equals(500, err.code)
            self.assert_equals("500 Server error, traceback not found", err.msg)
            return True
        assert False, "500 expected"
