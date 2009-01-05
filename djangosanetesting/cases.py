from django.test import TestCase as DjangoTestCase

from nose.tools import (
                assert_equals,
                assert_raises,
)


class SaneTestCase(object):
    start_live_server = False
    """ Common ancestor we're using our own hierarchy """
    
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
    
    def __init__(self):
        SaneTestCase.__init__(self)
    
    def setUp(self):
        SaneTestCase.setUp(self)

    def tearDown(self):
        SaneTestCase.tearDown(self)