"""
Various plugins for nose, that let us do our magic.
"""
import socket
import threading
import os

from django.core.handlers.wsgi import WSGIHandler
from django.core.servers import basehttp

import nose
from nose import SkipTest
from nose.plugins import Plugin

from djangosanetesting.cases import HttpTestCase, DatabaseTestCase, DestructiveDatabaseTestCase
from djangosanetesting.selenium.driver import selenium

__all__ = ("LiveHttpServerRunnerPlugin", "DjangoPlugin", "SeleniumPlugin",)

def flush_database(case):
    from django.test.testcases import call_command
    from django.core import mail
    # there is a need for check if fixtures were involved (= same fixture?)
    call_command('flush', verbosity=0, interactive=False)
    if hasattr(case, 'fixtures'):
        # We have to use this slightly awkward syntax due to the fact
        # that we're using *args and **kwargs together.
        call_command('loaddata', *self.fixtures, **{'verbosity': 0})
    if hasattr(case, 'urls'):
        case._old_root_urlconf = settings.ROOT_URLCONF
        settings.ROOT_URLCONF = case.urls
        clear_url_caches()
    mail.outbox = []
    
def flush_urlconf(case):
    if hasattr(case, '_old_root_urlconf'):
        settings.ROOT_URLCONF = case._old_root_urlconf
        clear_url_caches()

def get_test_case_class(nose_test):
    if isinstance(nose_test.test, nose.case.MethodTestCase):
        return nose_test.test.test.im_class
    else:
        return nose_test.test.__class__


class StoppableWSGIServer(basehttp.WSGIServer):
    """WSGIServer with short timeout, so that server thread can stop this server."""

    def server_bind(self):
        """Sets timeout to 1 second."""
        basehttp.WSGIServer.server_bind(self)
        self.socket.settimeout(1)

    def get_request(self):
        """Checks for timeout when getting request."""
        try:
            sock, address = self.socket.accept()
            sock.settimeout(None)
            return (sock, address)
        except socket.timeout:
            raise

class TestServerThread(threading.Thread):
    """Thread for running a http server while tests are running."""

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self._stopevent = threading.Event()
        self.started = threading.Event()
        self.error = None
        super(TestServerThread, self).__init__()

    def run(self):
        """Sets up test server and database and loops over handling http requests."""
        try:
            handler = basehttp.AdminMediaHandler(WSGIHandler())
            server_address = (self.address, self.port)
            httpd = StoppableWSGIServer(server_address, basehttp.WSGIRequestHandler)
            httpd.set_app(handler)
            self.started.set()
        except basehttp.WSGIServerException, e:
            self.error = e
            self.started.set()
            return

        # Must do database stuff in this new thread if database in memory.
        from django.conf import settings
        if settings.DATABASE_ENGINE == 'sqlite3' \
            and (not settings.TEST_DATABASE_NAME or settings.TEST_DATABASE_NAME == ':memory:'):
            raise SkipTest("You're running database in memory, but trying to use live server in another thread. Skipping.")
        
        # Loop until we get a stop event.
        while not self._stopevent.isSet():
            httpd.handle_request()

    def join(self, timeout=None):
        """Stop the thread and wait for it to finish."""
        self._stopevent.set()
        threading.Thread.join(self, timeout)

class LiveHttpServerRunnerPlugin(Plugin):
    """
    Patch Django on fly and start live HTTP server, if TestCase is inherited
    from HttpTestCase or start_live_server attribute is set to True.
    
    Taken from Michael Rogers implementation from http://trac.getwindmill.com/browser/trunk/windmill/authoring/djangotest.py
    """
    name = 'djangoliveserver'
    activation_parameter = '--with-djangoliveserver'
    
    def __init__(self):
        super(self.__class__, self).__init__()
        self.server_started = False
        self.server_thread = None
        
    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env)

    def configure(self, options, config):
        Plugin.configure(self, options, config)
        
    def startTest(self, test):
        cls = get_test_case_class(test)
        if not self.server_started and (issubclass(cls, HttpTestCase) or (hasattr(cls, "start_live_server") and cls.start_live_server)):
            self.start_server()
            self.server_started = True

    def start_server(self, address='0.0.0.0', port=8000):
        self.server_thread = TestServerThread(address, port)
        self.server_thread.start()
        self.server_thread.started.wait()
        if self.server_thread.error:
            raise self.server_thread.error

    def stop_test_server(self):
        if self.server_thread:
            self.server_thread.join()

class DjangoPlugin(Plugin):
    """
    Setup and teardown django test environment
    """
    activation_parameter = '--with-django'
    name = 'django'

    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env)

    def configure(self, options, config):
        Plugin.configure(self, options, config)
    
    def begin(self):
        """
        Before running database, initialize database et al, so noone will complain
        """
        from django.test.utils import setup_test_environment
        setup_test_environment()
        
        #FIXME: This should be perhaps moved to startTest and be lazy
        # for tests that do not need test database at all
        import settings
        from django.db import connection
        self.old_name = settings.DATABASE_NAME
        
        connection.creation.create_test_db(verbosity=False, autoclobber=True)
    
    def finalize(self, *args, **kwargs):
        """
        At the end, tear down our testbed
        """
        from django.test.utils import teardown_test_environment
        teardown_test_environment()

        import settings
        from django.db import connection
        connection.creation.destroy_test_db(self.old_name, verbosity=False)
    
    
    def startTest(self, test):
        """
        When preparing test, check whether to make our database fresh
        """
        from django.db import transaction
        
        from cases import DatabaseTestCase
        
        # this only works for methods and is strange, I know
        # report if you have better idea how to access original testcase instance
        test_case = get_test_case_class(test)
        
        if (hasattr(test_case, "database_single_transaction") and test_case.database_single_transaction is True):
            transaction.enter_transaction_management()
            transaction.managed(True)
        
        if (hasattr(test_case, "database_flush") and test_case.database_flush is True):
            flush_database(self)

    def stopTest(self, test):
        """
        After test is run, clear urlconf and caches
        """
        from django.db import transaction
        
        test_case = get_test_case_class(test)
        
        if (hasattr(test_case, "database_single_transaction") and test_case.database_single_transaction is True):
            transaction.rollback()
            transaction.leave_transaction_management()

        flush_urlconf(self)

class SeleniumPlugin(Plugin):
    """
    For testcases with selenium_start set to True, connect to Selenium RC.
    """
    activation_parameter = '--with-selenium'
    name = 'selenium'
    
    score = 120
    
    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env)

    def configure(self, options, config):
        Plugin.configure(self, options, config)

    def startTest(self, test):
        """
        When preparing test, check whether to make our database fresh
        """

        from django.conf import settings
        
        test_case = get_test_case_class(test)
        if getattr(test_case, "selenium_start", False):
            sel = selenium(
                      getattr(settings, "SELENIUM_HOST", 'localhost'),
                      int(getattr(settings, "SELENIUM_PORT", 4444)),
                      getattr(settings, "SELENIUM_BROWSER_COMMAND", '*opera'),
                      getattr(settings, "SELENIUM_URL_ROOT", getattr(settings, "URL_ROOT", "http://localhost:8000/")),
                  ) 
            try:
                sel.start()
            except Exception, err:
                # we must catch it all as there is untyped socket exception on Windows :-]]]
                if getattr(settings, "FORCE_SELENIUM_TESTS", False):
                    raise
                else:
                    raise SkipTest(err)
            else:
                if isinstance(test.test, nose.case.MethodTestCase):
                    test.test.test.im_self.selenium = sel
                else:
                    raise SkipTest("I can only assign selenium to TestCase instance; argument passing will be implemented later")
    
    def stopTest(self, test):
        test_case = get_test_case_class(test)
        if getattr(test_case, "selenium_start", False):
            test.test.test.im_self.selenium.stop()
            test.test.test.im_self.selenium = None

