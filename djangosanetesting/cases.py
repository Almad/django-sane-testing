from django.test import TestCase as DjangoTestCase

class SaneTestCase(object):
    start_live_server = False
    """ Common ancestor we're using our own hierarchy """

class HttpTestCase(SaneTestCase, DjangoTestCase):
    start_live_server = False
    """
    If it is not running, our plugin should start HTTP server
    so we can use it with urllib2 or some webtester.
    """
