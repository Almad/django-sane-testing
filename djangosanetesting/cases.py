from django.core.urlresolvers import clear_url_caches
from nose.tools import (
                assert_equals,
                assert_raises,
)

class SaneTestCase(object):
    """ Common ancestor we're using our own hierarchy """
    start_live_server = False
    database_single_transaction = False
    database_flush = False
    selenium_start = False
    
    def setUp(self):
        pass
    
    def assert_equals(self, *args, **kwargs):
        assert_equals(*args, **kwargs)
    
    assertEquals = assert_equals
    
    def assert_raises(self, *args, **kwargs):
        assert_raises(*args, **kwargs)
    
    assertRaises = assert_raises
    
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

