"""
Various plugins for nose, that let us do our magic.
"""
import socket
import threading
import os
from BaseHTTPServer import HTTPServer
from SocketServer import ThreadingMixIn
from time import sleep

from django.core.handlers.wsgi import WSGIHandler
from django.core.servers.basehttp import  WSGIRequestHandler, AdminMediaHandler, WSGIServerException

import nose
from nose import SkipTest
from nose.plugins import Plugin

from djangosanetesting.cases import HttpTestCase, DatabaseTestCase, DestructiveDatabaseTestCase
from djangosanetesting.selenium.driver import selenium

__all__ = ("CherryPyLiveServerPlugin", "DjangoLiveServerPlugin", "DjangoPlugin", "SeleniumPlugin", "SaneTestSelectionPlugin")

def flush_urlconf(case):
    if hasattr(case, '_old_root_urlconf'):
        settings.ROOT_URLCONF = case._old_root_urlconf
        clear_url_caches()

def get_test_case_class(nose_test):
    if isinstance(nose_test.test, nose.case.MethodTestCase):
        return nose_test.test.test.im_class
    else:
        return nose_test.test.__class__

def get_test_case_instance(nose_test):
    if isinstance(nose_test.test, nose.case.MethodTestCase):
        return nose_test.test.test.im_self
    else:
        return None

def enable_test(test_case, plugin_attribute):
    if not getattr(test_case, plugin_attribute, False):
        setattr(test_case, plugin_attribute, True)

#####
### Okey, this is hack because of #14, or Django's #3357
### We could runtimely patch basehttp.WSGIServer to inherit from our HTTPServer,
### but we'd like to have our own modifications anyway, so part of it is cut & paste
### from basehttp.WSGIServer.
### Credits & Kudos to Django authors and Rob Hudson et al from #3357
#####

class StoppableWSGIServer(ThreadingMixIn, HTTPServer):
    """WSGIServer with short timeout, so that server thread can stop this server."""
    application = None
    
    def __init__(self, server_address, RequestHandlerClass=None):
        HTTPServer.__init__(self, server_address, RequestHandlerClass) 
    
    def server_bind(self):
        """ Bind server to socket. Overrided to store server name & set timeout"""
        try:
            HTTPServer.server_bind(self)
        except Exception, e:
            raise WSGIServerException, e
        self.setup_environ()
        self.socket.settimeout(1)

    def get_request(self):
        """Checks for timeout when getting request."""
        try:
            sock, address = self.socket.accept()
#            sock.settimeout(None)
            return (sock, address)
        except socket.timeout:
            raise

    #####
    ### Code from basehttp.WSGIServer follows
    #####
    def setup_environ(self):
        # Set up base environment
        env = self.base_environ = {}
        env['SERVER_NAME'] = self.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PORT'] = str(self.server_port)
        env['REMOTE_HOST']=''
        env['CONTENT_LENGTH']=''
        env['SCRIPT_NAME'] = ''

    def get_app(self):
        return self.application

    def set_app(self,application):
        self.application = application

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
        """Sets up test server and loops over handling http requests."""
        try:
            handler = AdminMediaHandler(WSGIHandler())
            server_address = (self.address, self.port)
            httpd = StoppableWSGIServer(server_address, WSGIRequestHandler)
            #httpd = basehttp.WSGIServer(server_address, basehttp.WSGIRequestHandler)
            httpd.set_app(handler)
            self.started.set()
        except WSGIServerException, e:
            self.error = e
            self.started.set()
            return

        # When using memory database, complain as we'd use indepenent databases
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

class AbstractLiveServerPlugin(Plugin):
    def __init__(self):
        Plugin.__init__(self)
        self.server_started = False
        self.server_thread = None

    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env)

    def configure(self, options, config):
        Plugin.configure(self, options, config)
    
    def start_server(self):
        raise NotImplementedError()

    def stop_server(self):
        raise NotImplementedError()
    
    def startTest(self, test):
        test_case = get_test_case_class(test)
        test_instance = get_test_case_instance(test)
        if not self.server_started and getattr(test_case, "start_live_server", False):
            self.start_server()
            self.server_started = True
            
        enable_test(test_case, 'http_plugin_started')
            
        # clear test client for test isolation
        if test_instance:
            test_instance.client = None
    
    def finalize(self, result):
        self.stop_test_server()

class DjangoLiveServerPlugin(AbstractLiveServerPlugin):
    """
    Patch Django on fly and start live HTTP server, if TestCase is inherited
    from HttpTestCase or start_live_server attribute is set to True.
    
    Taken from Michael Rogers implementation from http://trac.getwindmill.com/browser/trunk/windmill/authoring/djangotest.py
    """
    name = 'djangoliveserver'
    activation_parameter = '--with-djangoliveserver'
    
    def start_server(self, address='0.0.0.0', port=8000):
        self.server_thread = TestServerThread(address, port)
        self.server_thread.start()
        self.server_thread.started.wait()
        if self.server_thread.error:
            raise self.server_thread.error
         
    def stop_test_server(self):
        if self.server_thread:
            self.server_thread.join()
        self.server_started = False

#####
### It was a nice try with Django server being threaded.
### It still sucks for some cases (did I mentioned urllib2?),
### so provide cherrypy as working alternative.
### Do imports in method to avoid CP as dependency
### Code originally written by Mikeal Rogers under Apache License.
#####

class CherryPyLiveServerPlugin(AbstractLiveServerPlugin):
    name = 'cherrypyliveserver'
    activation_parameter = '--with-cherrypyliveserver'

    def start_server(self, address='0.0.0.0', port=8000):
         _application = AdminMediaHandler(WSGIHandler())
    
         def application(environ, start_response):
             environ['PATH_INFO'] = environ['SCRIPT_NAME'] + environ['PATH_INFO']
             return _application(environ, start_response)
    
         from cherrypy.wsgiserver import CherryPyWSGIServer
         from threading import Thread
         self.httpd = CherryPyWSGIServer((address, port), application, server_name='django-test-http')
         self.httpd_thread = Thread(target=self.httpd.start)
         self.httpd_thread.start()
         #FIXME: This could be avoided by passing self to thread class starting django
         # and waiting for Event lock
         sleep(.5)
    
    def stop_test_server(self):
        if self.server_started:
            self.httpd.stop()
            self.server_started = False

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
        self.need_flush = False
    
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
        #####
        ### FIXME: Method is a bit ugly, would be nice to refactor if's to methods
        #####
        
        from django.db import transaction
        from django.test.testcases import call_command
        from django.core import mail
        
        test_case = get_test_case_class(test)
        self.previous_test_needed_flush = self.need_flush
        mail.outbox = []
        enable_test(test_case, 'django_plugin_started')
        
        # clear URLs if needed
        if hasattr(test_case, 'urls'):
            test_case._old_root_urlconf = settings.ROOT_URLCONF
            settings.ROOT_URLCONF = test_case.urls
            clear_url_caches()
        
        #####
        ### Database handling follows
        #####
        
        if getattr(test_case, 'no_database_interaction', False):
            # for true unittests, we can leave database handling for later,
            # as unittests by definition do not interacts
            return
        
        # make self.transaction available
        test_case.transaction = transaction
        self.commits_could_be_used = False
        
        if getattr(test_case, "database_flush", True):
            call_command('flush', verbosity=0, interactive=False)
            # it's possible that some garbage will be left after us, flush next time
            self.need_flush = True
            # commits are allowed during tests
            self.commits_could_be_used = True
            
        # previous test needed flush, clutter could have stayed in database
        elif self.previous_test_needed_flush is True:
            call_command('flush', verbosity=0, interactive=False)
            self.need_flush = False
        
        # otherwise we should have done our job
        else:
            self.need_flush = False
            
        
        if (hasattr(test_case, "database_single_transaction") and test_case.database_single_transaction is True):
            transaction.enter_transaction_management()
            transaction.managed(True)
        
        # fixtures are loaded inside transaction, thus we don't need to flush
        # between database_single_transaction tests when their fixtures differ
        if hasattr(test_case, 'fixtures'):
            if self.commits_could_be_used:
                commit = True
            else:
                commit = False
            call_command('loaddata', *test_case.fixtures, **{'verbosity': 0, 'commit' : commit})

        
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
    
    score = 80
    
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

        enable_test(test_case, 'selenium_plugin_started')
        
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

class SaneTestSelectionPlugin(Plugin):
    """ Accept additional options, so we can filter out test we don't want """
    RECOGNIZED_TESTS = ["unit", "database", "destructivedatabase", "http", "selenium"]
    score = 150
    
    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env)
        parser.add_option(
            "-u", "--select-unittests", action="store_true",
            default=False, dest="select_unittests",
            help="Run all unittests"
        )
        parser.add_option(
            "--select-databasetests", action="store_true",
            default=False, dest="select_databasetests",
            help="Run all database tests"
        )
        parser.add_option(
            "--select-destructivedatabasetests", action="store_true",
            default=False, dest="select_destructivedatabasetests",
            help="Run all destructive database tests"
        )
        parser.add_option(
            "--select-httptests", action="store_true",
            default=False, dest="select_httptests",
            help="Run all HTTP tests"
        )
        parser.add_option(
            "--select-seleniumtests", action="store_true",
            default=False, dest="select_seleniumtests",
            help="Run all Selenium tests"
        )

    def configure(self, options, config):
        Plugin.configure(self, options, config)
        self.enabled_tests = [i for i in self.RECOGNIZED_TESTS if getattr(options, "select_%stests" % i, False)]
    
    def startTest(self, test):
        test_case = get_test_case_class(test)
        if getattr(test_case, "test_type", "unit") not in self.enabled_tests:
            raise SkipTest(u"Test type %s not enabled" % getattr(test_case, "test_type", "unit"))

