# -*- coding: utf-8 -*-
import urllib2
from djangosanetesting.cases import HttpTestCase, SeleniumTestCase
from djangosanetesting.utils import get_live_server_path

from testapp.models import ExampleModel

class TestLiveServerRunning(HttpTestCase):
    
    def get_ok(self):
        self.assertEquals(u'OKidoki', self.urlopen('%stesttwohundred/' % get_live_server_path()).read())

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
                response = self.urlopen(url='%sreturn_not_authorized/' % get_live_server_path(), data='data')
                #response = opener.open(request)
            except urllib2.HTTPError, err:
                self.assert_equals(401, err.code)
            else:
                assert False, "401 expected"

    def test_server_error(self):
        try:
            self.urlopen(url='%sreturn_server_error/' % get_live_server_path())
        except urllib2.HTTPError, err:
            self.assert_equals(500, err.code)
            self.assert_equals("500 Server error, traceback not found", err.msg)
        else:
            assert False, "500 expected"

    def test_django_error_traceback(self):
        try:
            self.urlopen(url='%sreturn_django_error/' % get_live_server_path())
        except urllib2.HTTPError, err:
            self.assert_equals(500, err.code)
            self.assert_not_equals("500 Server error, traceback not found", err.msg)
        else:
            assert False, "500 expected"

class TestSelenium(SeleniumTestCase):
    translation_language_code = 'cs'

    def setUp(self):
        super(TestSelenium, self).setUp()
        from django.utils import translation
        translation.activate("cs")

    def test_ok(self):
        self.selenium.open("/testtwohundred/")
        self.assert_true(self.selenium.is_text_present("OKidoki"))

    def test_czech_string_acquired_even_with_selenium(self):
        self.assert_equals(u"Přeložitelný řetězec", unicode(ExampleModel.get_translated_string()))

    def test_selenium_server_error(self):
        try:
            self.selenium.open('/return_django_error/')
        except Exception, err:
            self.assert_not_equals("500 Server error, traceback not found", err.msg)
        else:
            self.fail("500 expected")

    def test_selenium_django_error_traceback(self):
        try:
            self.selenium.open('/return_server_error/')
        except Exception, err:
            self.assert_equals("500 Server error, traceback not found", err.msg)
        else:
            self.fail("500 expected")


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
        else:
            self.fail("500 expected")

    def test_twill_django_error_traceback(self):
        try:
            self.twill.go('/return_server_error/')
        except urllib2.HTTPError, err:
            self.assert_equals(500, err.code)
            self.assert_equals("500 Server error, traceback not found", err.msg)
        else:
            self.fail("500 expected")
