import re
import sys
import urllib2

from django.template import Context, Template, TemplateSyntaxError
from nose.tools import (
                assert_equals,
                assert_almost_equals,
                assert_not_equals,
                assert_raises,
                assert_true,
                assert_false,
)
from nose import SkipTest

from djangosanetesting.utils import twill_patched_go, twill_xpath_go, extract_django_traceback, get_live_server_path

__all__ = ("UnitTestCase", "DatabaseTestCase", "DestructiveDatabaseTestCase",
           "HttpTestCase", "SeleniumTestCase", "TemplateTagTestCase")

class SaneTestCase(object):
    """ Common ancestor we're using our own hierarchy """
    start_live_server = False
    database_single_transaction = False
    database_flush = False
    selenium_start = False
    no_database_interaction = False
    make_translations = True
    
    SkipTest = SkipTest

    failureException = AssertionError

    def __new__(type, *args, **kwargs):
        """
        When constructing class, add assert* methods from unittest(2),
        both camelCase and pep8-ify style.
        
        """
        obj = super(SaneTestCase, type).__new__(type, *args, **kwargs)

        caps = re.compile('([A-Z])')
        
        from django.test import TestCase
        
        ##########
        ### Scraping heavily inspired by nose testing framework, (C) by Jason Pellerin
        ### and respective authors.
        ##########
        
        class Dummy(TestCase):
            def att():
                pass
        t = Dummy('att')
        
        def pepify(name):
            return caps.sub(lambda m: '_' + m.groups()[0].lower(), name)
        
        def scrape(t):
            for a in [at for at in dir(t) if at.startswith('assert') and not '_' in at]:
                v = getattr(t, a)
                setattr(obj, a, v)
                setattr(obj, pepify(a), v)
        
        scrape(t)
        
        try:
            from unittest2 import TestCase
        except ImportError:
            pass
        else:
            class Dummy(TestCase):
                def att():
                    pass
            t = Dummy('att')
            scrape(t)
                
        return obj

    
    def _check_plugins(self):
        if getattr(self, 'required_sane_plugins', False):
            for plugin in self.required_sane_plugins:
                if not getattr(self, "%s_plugin_started" % plugin, False):
                    raise self.SkipTest("Plugin %s from django-sane-testing required, skipping" % plugin)

    def _check_skipped(self):
        if getattr(self, "skipped", False):
            raise self.SkipTest("I've been marked to skip myself")

    def setUp(self):
        self._check_skipped()
        self._check_plugins()
    

    def fail(self, *args, **kwargs):
        raise self.failureException(*args, **kwargs)

    def tearDown(self):
        pass

class UnitTestCase(SaneTestCase):
    """
    This class is a unittest, i.e. do not interact with database et al
    and thus not need any special treatment.
    """
    no_database_interaction = True
    test_type = "unit"


    # undocumented client: can be only used for views that are *guaranteed*
    # not to interact with models
    def get_django_client(self):
        from django.test import Client
        if not getattr(self, '_django_client', False):
            self._django_client = Client()
        return self._django_client

    def set_django_client(self, value):
        self._django_client = value

    client = property(fget=get_django_client, fset=set_django_client)



class DatabaseTestCase(SaneTestCase):
    """
    Tests using database for models in simple: rollback on teardown and we're out.
    
    However, we must check for fixture difference, if we're using another fixture, we must flush database anyway.
    """
    database_single_transaction = True
    database_flush = False
    required_sane_plugins = ["django"]
    django_plugin_started = False
    test_type = "database"

    def get_django_client(self):
        from django.test import Client
        if not getattr(self, '_django_client', False):
            self._django_client = Client()
        return self._django_client
    
    def set_django_client(self, value):
        self._django_client = value
    
    client = property(fget=get_django_client, fset=set_django_client)
    
    
class DestructiveDatabaseTestCase(DatabaseTestCase):
    """
    Test behaving so destructively that it needs database to be flushed.
    """
    database_single_transaction = True
    database_flush = True
    test_type = "destructivedatabase"

class HttpTestCase(DestructiveDatabaseTestCase):
    """
    If it is not running, our plugin should start HTTP server
    so we can use it with urllib2 or some webtester.
    """
    start_live_server = True
    required_sane_plugins = ["django", "http"]
    http_plugin_started = False
    test_type = "http"

    def __init__(self, *args, **kwargs):
        super(HttpTestCase, self).__init__(*args, **kwargs)

        self._twill = None
        self._spynner = None

    def get_twill(self):
        if not self._twill:
            try:
                import twill
            except ImportError:
                raise SkipTest("Twill must be installed if you want to use it")

            from twill import get_browser

            self._twill = get_browser()
            self._twill.go = twill_patched_go(browser=self._twill, original_go=self._twill.go)
            self._twill.go_xpath = twill_xpath_go(browser=self._twill, original_go=self._twill.go)

            from twill import commands
            self._twill.commands = commands

        return self._twill

    twill = property(fget=get_twill)

    def get_spynner(self):
        if not self._spynner:
            try:
                import spynner
            except ImportError:
                raise SkipTest("Spynner must be installed if you want to use it")

            self._spynner = spynner.Browser()

        return self._spynner

    spynner = property(fget=get_spynner)


    def assert_code(self, code):
        self.assert_equals(int(code), self.twill.get_code())

    def urlopen(self, *args, **kwargs):
        """
        Wrap for the urlopen function from urllib2
        prints django's traceback if server responds with 500
        """
        try:
            return urllib2.urlopen(*args, **kwargs)
        except urllib2.HTTPError, err:
            if err.code == 500:
                raise extract_django_traceback(http_error=err)
            else:
                raise err

    def tearDown(self):
        if self._spynner:
            self._spynner.close()

        super(HttpTestCase, self).tearDown()

class SeleniumTestCase(HttpTestCase):
    """
    Connect to selenium RC and provide it as instance attribute.
    Configuration in settings:
      * SELENIUM_HOST (default to localhost)
      * SELENIUM_PORT (default to 4444)
      * SELENIUM_BROWSER_COMMAND (default to *opera)
      * SELENIUM_URL_ROOT (default to URL_ROOT default to /)
    """
    selenium_start = True
    start_live_server = True
    required_sane_plugins = ["django", "selenium", "http"]
    selenium_plugin_started = False
    test_type = "selenium"


class TemplateTagTestCase(UnitTestCase):
    """
    Allow for sane and comfortable template tag unit-testing.

    Attributes:
    * `preload' defines which template tag libraries are to be loaded
      before rendering the actual template string
    * `TemplateSyntaxError' is bundled within this class, so that nothing
      from django.template must be imported in most cases of template
      tag testing
    """

    TemplateSyntaxError = TemplateSyntaxError
    preload = ()

    def render_template(self, template, **kwargs):
        """
        Render the given template string with user-defined tag modules
        pre-loaded (according to the class attribute `preload').
        """

        loads = u''
        for load in self.preload:
            loads = u''.join([loads, '{% load ', load, ' %}'])

        template = u''.join([loads, template])
        return Template(template).render(Context(kwargs))
