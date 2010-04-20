from nose.tools import (
                assert_equals,
                assert_almost_equals,
                assert_not_equals,
                assert_raises,
                assert_true,
                assert_false,
)
from nose import SkipTest

from djangosanetesting.utils import twill_patched_go

__all__ = ("UnitTestCase", "DatabaseTestCase", "DestructiveDatabaseTestCase", "HttpTestCase", "SeleniumTestCase")

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
    
    def assert_equals(self, *args, **kwargs):
        assert_equals(*args, **kwargs)
    
    assertEquals = assert_equals
    
    def assert_not_equals(self, *args, **kwargs):
        assert_not_equals(*args, **kwargs)
    
    assertNotEquals = assert_not_equals
    

    def assert_almost_equals(self, *args, **kwargs):
        assert_almost_equals(*args, **kwargs)
    
    assertAlmostEquals = assert_almost_equals
    
    def assert_raises(self, *args, **kwargs):
        assert_raises(*args, **kwargs)
    
    assertRaises = assert_raises

    def assert_true(self, *args, **kwargs):
        assert_true(*args, **kwargs)
    
    assertTrue = assert_true
    
    def assert_false(self, *args, **kwargs):
        assert_false(*args, **kwargs)
    
    assertFalse = assert_false

    def fail(self, *args, **kwargs):
        self.failureException(*args, **kwargs)

    def tearDown(self):
        pass

class UnitTestCase(SaneTestCase):
    """
    This class is a unittest, i.e. do not interact with database et al
    and thus not need any special treatment.
    """
    no_database_interaction = True
    test_type = "unit"
    
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

    def get_twill(self):
        if not self._twill:
            try:
                import twill
            except ImportError:
                raise SkipTest("Twill must be installed if You want to use it")

            from twill import get_browser

            self._twill = get_browser()
            self._twill.go = twill_patched_go(self._twill.go)

        return self._twill

    twill = property(fget=get_twill)
    
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

