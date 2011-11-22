"""
Various plugins for nose, that let us do our magic.
"""
import socket
import threading
import os
from BaseHTTPServer import HTTPServer
from SocketServer import ThreadingMixIn
from time import sleep
from inspect import ismodule, isclass
import unittest

from django.core.management import call_command
from django.core.handlers.wsgi import WSGIHandler
from django.core.servers.basehttp import  WSGIRequestHandler, AdminMediaHandler, WSGIServerException
from django.core.urlresolvers import clear_url_caches

import nose
from nose.plugins import Plugin

import djangosanetesting
from djangosanetesting import MULTIDB_SUPPORT, DEFAULT_DB_ALIAS
from djangosanetesting.cache import flush_django_cache

#from djagnosanetesting.cache import flush_django_cache
from djangosanetesting.selenium.driver import selenium
from djangosanetesting.utils import (
    get_live_server_path, test_database_exists,
    DEFAULT_LIVE_SERVER_ADDRESS, DEFAULT_LIVE_SERVER_PORT,
)
TEST_CASE_CLASSES = (djangosanetesting.cases.SaneTestCase, unittest.TestCase)

__all__ = ("CherryPyLiveServerPlugin", "DjangoLiveServerPlugin", "DjangoPlugin", "SeleniumPlugin", "SaneTestSelectionPlugin", "ResultPlugin")



def flush_cache(test=None):
    from django.contrib.contenttypes.models import ContentType
    ContentType.objects.clear_cache()

    from django.conf import settings

    if (test and getattr_test(test, "flush_django_cache", False)) \
        or (not hasattr_test(test, "flush_django_cache") and getattr(settings, "DST_FLUSH_DJANGO_CACHE", False)):
        flush_django_cache()

def is_test_case_class(nose_test):
    if isclass(nose_test) and issubclass(nose_test, TEST_CASE_CLASSES):
        return True
    else:
        return False

def get_test_case_class(nose_test):
    if ismodule(nose_test) or is_test_case_class(nose_test):
        return nose_test 
    if isinstance(nose_test.test, nose.case.MethodTestCase):
        return nose_test.test.test.im_class
    else:
        return nose_test.test.__class__

def get_test_case_method(nose_test):
    if not hasattr(nose_test, 'test'): # not test method/functoin, probably test module or test class (from startContext)
        return None
    if isinstance(nose_test.test, (nose.case.MethodTestCase, nose.case.FunctionTestCase)):
        return nose_test.test.test
    else:
        return getattr(nose_test.test, nose_test.test._testMethodName)

def get_test_case_instance(nose_test):
    if ismodule(nose_test) or is_test_case_class(nose_test):
        return nose_test 
    if getattr(nose_test, 'test') and not isinstance(nose_test.test, (nose.case.FunctionTestCase)):
        return get_test_case_method(nose_test).im_self

def hasattr_test(nose_test, attr_name):
    ''' hasattr from test method or test_case.
    '''

    if nose_test is None:
        return False
    elif ismodule(nose_test) or is_test_case_class(nose_test):
        return hasattr(nose_test, attr_name)
    elif hasattr(get_test_case_method(nose_test), attr_name) or hasattr(get_test_case_instance(nose_test), attr_name):
        return True
    else:
        return False

def getattr_test(nose_test, attr_name, default = False):
    ''' Get attribute from test method, if not found then form it's test_case instance
        (meaning that test method have higher priority). If not found even
        in test_case then return default.
    '''
    test_attr = getattr(get_test_case_method(nose_test), attr_name, None)
    if test_attr is not None:
        return test_attr
    else:
        return getattr(get_test_case_instance(nose_test), attr_name, default)

def enable_test(test_case, plugin_attribute):
    if not getattr(test_case, plugin_attribute, False):
        setattr(test_case, plugin_attribute, True)

def flush_database(test_case, database=DEFAULT_DB_ALIAS):
    call_command('flush', verbosity=0, interactive=False, database=database)


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

    def check_database_multithread_compilant(self):
        # When using memory database, complain as we'd use indepenent databases
        from django.conf import settings
        if settings.DATABASE_ENGINE == 'sqlite3' \
            and (not getattr(settings, 'TEST_DATABASE_NAME', False) or settings.TEST_DATABASE_NAME == ':memory:'):
            self.skipped = True
            return False
            #raise SkipTest("You're running database in memory, but trying to use live server in another thread. Skipping.")
        return True

    def startTest(self, test):
        from django.conf import settings
        test_case = get_test_case_class(test)
        test_case_instance = get_test_case_instance(test)
        if not self.server_started and getattr_test(test, "start_live_server", False):
            if not self.check_database_multithread_compilant():
                return
            self.start_server(
                address=getattr(settings, "LIVE_SERVER_ADDRESS", DEFAULT_LIVE_SERVER_ADDRESS),
                port=int(getattr(settings, "LIVE_SERVER_PORT", DEFAULT_LIVE_SERVER_PORT))
            )
            self.server_started = True
            
        enable_test(test_case, 'http_plugin_started')
        
        # clear test client for test isolation
        if test_case_instance:
            test_case_instance.client = None

    def stopTest(self, test):
        test_case_instance = get_test_case_instance(test)
        if getattr_test(test, "_twill", None):
            from twill.commands import reset_browser
            reset_browser()
            test_case_instance._twill = None

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
    env_opt = 'DST_PERSIST_TEST_DATABASE'

    def startContext(self, context):
        if ismodule(context) or is_test_case_class(context):
            if ismodule(context):
                attr_suffix = ''
            else:
                attr_suffix = '_after_all_tests'
            if getattr(context, 'database_single_transaction' + attr_suffix, False) \
                or getattr(context, 'fixtures', None):
                #TODO: When no test case in this module needing database is run (for example 
                #      user selected only one unitTestCase), database should not be initialized.
                #      So it would be best if db is initialized when first test case needing 
                #      database is run. 
                
                # create test database if not already created
                if not self.test_database_created:
                    self._create_test_databases()

                if getattr(context, 'database_single_transaction' + attr_suffix, False):
                    from django.db import transaction
                    transaction.enter_transaction_management()
                    transaction.managed(True)

                # when used from startTest, nose-wrapped testcase is provided -- while now,
                # we have 'bare' test case.

                self._prepare_tests_fixtures(context)

    def stopContext(self, context):
        if ismodule(context) or is_test_case_class(context):
            from django.conf import settings
            from django.db import transaction

            if ismodule(context):
                attr_suffix = ''
            else:
                attr_suffix = '_after_all_tests'

            if self.test_database_created:
                if getattr(context, 'database_single_transaction' + attr_suffix, False):
                    transaction.rollback()
                    transaction.leave_transaction_management()

                if getattr(context, "database_flush" + attr_suffix, None):
                    for db in self._get_tests_databases(getattr(context, 'multidb', False)):
                        getattr(settings, "TEST_DATABASE_FLUSH_COMMAND", flush_database)(self, database=db)

    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env)
        
        parser.add_option(
            "", "--persist-test-database", action="store_true",
            default=env.get(self.env_opt), dest="persist_test_database",
            help="Do not flush database unless neccessary [%s]" % self.env_opt)

    def configure(self, options, config):
        Plugin.configure(self, options, config)
        self.persist_test_database = options.persist_test_database

    def setup_databases(self, verbosity, autoclobber, **kwargs):
        # Taken from Django 1.2 code, (C) respective Django authors. Modified for backward compatibility by me
        connections = self._get_databases()
        old_names = []
        mirrors = []

        from django.conf import settings
        if 'south' in settings.INSTALLED_APPS:
            from south.management.commands import patch_for_test_db_setup

            settings.SOUTH_TESTS_MIGRATE = getattr(settings, 'DST_RUN_SOUTH_MIGRATIONS', True)
            patch_for_test_db_setup()

        for alias in connections:
            connection = connections[alias]
            # If the database is a test mirror, redirect it's connection
            # instead of creating a test database.
            if 'TEST_MIRROR' in connection.settings_dict and connection.settings_dict['TEST_MIRROR']:
                mirrors.append((alias, connection))
                mirror_alias = connection.settings_dict['TEST_MIRROR']
                connections._connections[alias] = connections[mirror_alias]
            else:
                if 'NAME' in connection.settings_dict:
                    old_names.append((connection, connection.settings_dict['NAME']))
                else:
                    old_names.append((connection, connection.settings_dict['DATABASE_NAME']))
                connection.creation.create_test_db(verbosity=verbosity, autoclobber=autoclobber)
        return old_names, mirrors

    def teardown_databases(self, old_config, verbosity, **kwargs):
        # Taken from Django 1.2 code, (C) respective Django authors
        connections = self._get_databases()
        old_names, mirrors = old_config
        # Point all the mirrors back to the originals
        for alias, connection in mirrors:
            connections._connections[alias] = connection
        # Destroy all the non-mirror databases
        for connection, old_name in old_names:
            connection.creation.destroy_test_db(old_name, verbosity)
        
        self.test_database_created = False

    def begin(self):
        from django.test.utils import setup_test_environment
        setup_test_environment()
        self.test_database_created = False

    def prepareTestRunner(self, runner):
        """
        Before running tests, initialize database et al, so noone will complain
        """
        # FIXME: this should be lazy for tests that do not need test
        # database at all
        
        from django.conf import settings
        self.old_name = settings.DATABASE_NAME

        flush_cache()

    def finalize(self, result):
        """
        At the end, tear down our testbed
        """
        from django.test.utils import teardown_test_environment
        teardown_test_environment()
        
        if not self.persist_test_database and getattr(self, 'test_database_created', None):
            self.teardown_databases(self.old_config, verbosity=False)
#            from django.db import connection
#            connection.creation.destroy_test_db(self.old_name, verbosity=False)
    
    
    def startTest(self, test):
        """
        When preparing test, check whether to make our database fresh
        """
        #####
        ### FIXME: It would be nice to separate handlings as plugins et al...but what 
        ### about the context?
        #####
        
        from django.core import mail
        from django.conf import settings
        from django.db import transaction
        
        test_case = get_test_case_class(test)
        test_case_instance = get_test_case_instance(test)
        mail.outbox = []
        enable_test(test_case, 'django_plugin_started')
        
        if hasattr(test_case_instance, 'is_skipped') and test_case_instance.is_skipped():
            return
        
        # clear URLs if needed
        if hasattr(test_case, 'urls'):
            test_case._old_root_urlconf = settings.ROOT_URLCONF
            settings.ROOT_URLCONF = test_case.urls
            clear_url_caches()
        
        #####
        ### Database handling follows
        #####
        if getattr_test(test, 'no_database_interaction', False):
            # for true unittests, we can leave database handling for later,
            # as unittests by definition do not interacts with database
            return
        
        # create test database if not already created
        if not self.test_database_created:
            self._create_test_databases()
        
        # make self.transaction available
        test_case.transaction = transaction
        
        if getattr_test(test, 'database_single_transaction'):
            transaction.enter_transaction_management()
            transaction.managed(True)
        
        self._prepare_tests_fixtures(test)
        
    def stopTest(self, test):
        """
        After test is run, clear urlconf, caches and database
        """
        from django.db import transaction
        from django.conf import settings

        test_case = get_test_case_class(test)
        test_case_instance = get_test_case_instance(test)

        if hasattr(test_case_instance, 'is_skipped') and test_case_instance.is_skipped():
            return

        if hasattr(test_case, '_old_root_urlconf'):
            settings.ROOT_URLCONF = test_case._old_root_urlconf
            clear_url_caches()
        flush_cache(test)

        if getattr_test(test, 'no_database_interaction', False):
            # for true unittests, we can leave database handling for later,
            # as unittests by definition do not interacts with database
            return
        
        if getattr_test(test, 'database_single_transaction'):
            transaction.rollback()
            transaction.leave_transaction_management()

        if getattr_test(test, "database_flush", True):
            for db in self._get_tests_databases(getattr_test(test, 'multi_db')):
                getattr(settings, "TEST_DATABASE_FLUSH_COMMAND", flush_database)(self, database=db)

    def _get_databases(self):
        try:
            from django.db import connections
        except ImportError:
            from django.db import connection
            connections = {DEFAULT_DB_ALIAS : connection}
        return connections

    def _get_tests_databases(self, multi_db):
        ''' Get databases for flush: according to test's multi_db attribute
            only defuault db or all databases will be flushed.
        '''
        connections = self._get_databases()
        if multi_db:
            if not MULTIDB_SUPPORT:
                raise RuntimeError('This test should be skipped but for a reason it is not')
            else:
                databases = connections
        else:
            if MULTIDB_SUPPORT:
                databases = [DEFAULT_DB_ALIAS]
            else:
                databases = connections
        return databases
    
    def _prepare_tests_fixtures(self, test):
        # fixtures are loaded inside transaction, thus we don't need to flush
        # between database_single_transaction tests when their fixtures differ
        if hasattr_test(test, 'fixtures'):
            if getattr_test(test, "database_flush", True):
                # commits are allowed during tests
                commit = True
            else:
                commit = False
            for db in self._get_tests_databases(getattr_test(test, 'multi_db')):
                call_command('loaddata', *getattr_test(test, 'fixtures'), **{'verbosity': 0, 'commit' : commit, 'database' : db})

    def _create_test_databases(self):
        from django.conf import settings
        connections = self._get_databases()
        if not self.persist_test_database or test_database_exists():
            #connection.creation.create_test_db(verbosity=False, autoclobber=True)
            self.old_config = self.setup_databases(verbosity=False, autoclobber=True)
            self.test_database_created = True
            
            for db in connections:
                if 'south' in settings.INSTALLED_APPS and getattr(settings, 'DST_RUN_SOUTH_MIGRATIONS', True):
                    call_command('migrate', database=db)
                
                if getattr(settings, "FLUSH_TEST_DATABASE_AFTER_INITIAL_SYNCDB", False):
                    getattr(settings, "TEST_DATABASE_FLUSH_COMMAND", flush_database)(self, database=db)


class DjangoTranslationPlugin(Plugin):
    """
    For testcases with selenium_start set to True, connect to Selenium RC.
    """
    activation_parameter = '--with-djangotranslations'
    name = 'djangotranslations'

    score = 70

    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env)

    def configure(self, options, config):
        Plugin.configure(self, options, config)

    def startTest(self, test):
        # set translation, if allowed
        if getattr_test(test, "make_translations", None):
            from django.conf import settings
            from django.utils import translation
            lang = getattr_test(test, "translation_language_code", None)
            if not lang:
                lang = getattr(settings, "LANGUAGE_CODE", 'en-us')
            translation.activate(lang)

    def stopTest(self, test):
        from django.utils import translation
        translation.deactivate()


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
        from django.utils.importlib import import_module

        test_case = get_test_case_class(test)

        enable_test(test_case, 'selenium_plugin_started')

        # import selenium class to use
        selenium_import = getattr(settings, "DST_SELENIUM_DRIVER",
                            "djangosanetesting.selenium.driver.selenium").split(".")
        selenium_module, selenium_cls = ".".join(selenium_import[:-1]), selenium_import[-1]
        selenium = getattr(import_module(selenium_module), selenium_cls)
        
        if getattr_test(test, "selenium_start", False):
            sel = selenium(
                      getattr(settings, "SELENIUM_HOST", 'localhost'),
                      int(getattr(settings, "SELENIUM_PORT", 4444)),
                      getattr(settings, "SELENIUM_BROWSER_COMMAND", '*opera'),
                      getattr(settings, "SELENIUM_URL_ROOT", get_live_server_path()),
                  )
            try:
                sel.start()
                test_case.selenium_started = True
            except Exception, err:
                # we must catch it all as there is untyped socket exception on Windows :-]]]
                if getattr(settings, "FORCE_SELENIUM_TESTS", False):
                    raise
                else:
                    test_case.skipped = True
                    #raise SkipTest(err)
            else:
                if isinstance(test.test, nose.case.MethodTestCase):
                    test.test.test.im_self.selenium = sel
                else:
                    test_case.skipped = True
                    #raise SkipTest("I can only assign selenium to TestCase instance; argument passing will be implemented later")

    def stopTest(self, test):
        if getattr_test(test, "selenium_started", False):
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
        if getattr_test(test, "test_type", "unit") not in self.enabled_tests:
            test_case.skipped = True
            #raise SkipTest(u"Test type %s not enabled" % getattr(test_case, "test_type", "unit"))

##########
### Result plugin is used when using Django test runner
### Taken from django-nose project.
### (C) Jeff Balogh and contributors, released under BSD license.
##########

class ResultPlugin(Plugin):
    """
    Captures the TestResult object for later inspection.

    nose doesn't return the full test result object from any of its runner
    methods.  Pass an instance of this plugin to the TestProgram and use
    ``result`` after running the tests to get the TestResult object.
    """

    name = "djangoresult"
    activation_parameter = '--with-djangoresult'
    enabled = True

    def configure(self, options, config):
        Plugin.configure(self, options, config)

    def finalize(self, result):
        self.result = result

