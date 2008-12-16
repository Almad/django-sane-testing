from django.test import TestCase as DjangoTestCase

class SaneTestCase(object):
    start_live_server = False
    """ Common ancestor we're using our own hierarchy """

class HttpTestCase(SaneTestCase, DjangoTestCase):
    start_live_server = True
    """
    If it is not running, our plugin should start HTTP server
    so we can use it with urllib2 or some webtester.
    """
    
    def __init__(self):
        DjangoTestCase.__init__(self)
        SaneTestCase.__init__(self)
    
    def setUp(self):
        DjangoTestCase.setUp(self)
        SaneTestCase.setUp(self)

    def tearDown(self):
        DjangoTestCase.tearDown(self)
        SaneTestCase.tearDown(self)