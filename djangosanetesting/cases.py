from django.core.urlresolvers import clear_url_caches
from nose.tools import (
                assert_equals,
                assert_almost_equals,
                assert_raises,
                assert_true,
                assert_false,
)
from nose import SkipTest

class SaneTestCase(object):
    """ Common ancestor we're using our own hierarchy """
    start_live_server = False
    database_single_transaction = False
    database_flush = False
    selenium_start = False
    
    SkipTest = SkipTest
    
    def _check_plugins(self):
        if getattr(self, 'required_sane_plugins', False):
            for plugin in self.required_sane_plugins:
                if not getattr(self, "%s_plugin_started", False):
                    raise self.SkipTest("Plugin %s from django-sane-testing required, skipping")
    
    def setUp(self):
        self._check_plugins()
    
    def assert_equals(self, *args, **kwargs):
        assert_equals(*args, **kwargs)
    
    assertEquals = assert_equals

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
    
    def tearDown(self):
        pass

class UnitTestCase(SaneTestCase):
    """
    This class is a unittest, i.e. do not interact with database et al
    and thus not need any special treatment.
    """
    
class DatabaseTestCase(SaneTestCase):
    """
    Tests using database for models in simple: rollback on teardown and we're out.
    
    However, we must check for fixture difference, if we're using another fixture, we must flush database anyway.
    """
    database_single_transaction = True
    database_flush = False
    required_sane_plugins = ["django"]
    django_plugin_started = False
    
class DestructiveDatabaseTestCase(DatabaseTestCase):
    """
    Test behaving so destructively that it needs database to be flushed.
    """
    database_single_transaction = True
    database_flush = True

class HttpTestCase(DestructiveDatabaseTestCase):
    """
    If it is not running, our plugin should start HTTP server
    so we can use it with urllib2 or some webtester.
    """
    start_live_server = True
    required_sane_plugins = ["django", "http"]
    http_plugin_started = False

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

