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
    
class HttpTestCase(SaneTestCase):
    start_live_server = True
    """
    If it is not running, our plugin should start HTTP server
    so we can use it with urllib2 or some webtester.
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

