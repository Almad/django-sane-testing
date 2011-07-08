import os
from functools import wraps
import urllib2

DEFAULT_LIVE_SERVER_PROTOCOL = "http"
DEFAULT_LIVE_SERVER_PORT = 8000
DEFAULT_LIVE_SERVER_ADDRESS = '0.0.0.0'
DEFAULT_URL_ROOT_SERVER_ADDRESS = 'localhost'


def extract_django_traceback(twill=None, http_error=None, lines=None):
    record = False
    traceback = ''

    if not lines and http_error:
        lines = http_error.readlines()
    elif twill:
        http_error = urllib2.HTTPError(url=twill.get_url(), code=500, msg=None, hdrs=None, fp=None)
        if not lines:
            lines = twill.result.get_page().split("\n")
    
    lines = lines or []

    for one in lines:
        if one.strip().startswith('<textarea ') and one.find('id="traceback_area"'):
            record = True
            continue
        if record and one.strip() == '</textarea>':
            break
        elif record:
            traceback += one.rstrip() + "\n"

    if record:
        http_error.msg = traceback
    else:
        http_error.msg = "500 Server error, traceback not found"

    return http_error

def is_test_database():
    """
    Return whether we're using test database. Can be used to determine if we're
    running tests.
    """
    from django.conf import settings

    # This is hacky, but fact we're running tests is determined by _create_test_db call.
    # We'll assume usage of it if assigned to settings.DATABASE_NAME

    if settings.TEST_DATABASE_NAME:
        test_database_name = settings.TEST_DATABASE_NAME
    else:
        from django.db import TEST_DATABASE_PREFIX
        test_database_name = TEST_DATABASE_PREFIX + settings.DATABASE_NAME

    return settings.DATABASE_NAME == test_database_name

def test_database_exists():
    from django.db import connection, DatabaseError
    from django.conf import settings

    try:
        if getattr(settings, "DATABASE_ENGINE", None) == 'sqlite3':
            if not os.path.exists(settings.DATABASE_NAME):
                raise DatabaseError()
        connection.cursor()
        return True
    except DatabaseError, err:
        return False

def get_live_server_path():
    from django.conf import settings

    return getattr(settings, "URL_ROOT", "%s://%s:%s/" % (
        getattr(settings, "LIVE_SERVER_PROTOCOL", DEFAULT_LIVE_SERVER_PROTOCOL),
        getattr(settings, "URL_ROOT_SERVER_ADDRESS", DEFAULT_URL_ROOT_SERVER_ADDRESS),
        getattr(settings, "LIVE_SERVER_PORT", DEFAULT_LIVE_SERVER_PORT)
    ))

def twill_patched_go(browser, original_go):
    """
    If call is not beginning with http, prepent it with get_live_server_path
    to allow relative calls
    """
    def twill_go_with_relative_paths(uri, *args, **kwargs):
        if not uri.startswith("http"):
            base = get_live_server_path()
            if uri.startswith("/"):
                base = base.rstrip("/")
            uri = "%s%s" % (base, uri)
        response = original_go(uri, *args, **kwargs)
        if browser.result.get_http_code() == 500:
            raise extract_django_traceback(twill=browser)
        else:
            return response
    return twill_go_with_relative_paths

def twill_xpath_go(browser, original_go):
    """
    If call is not beginning with http, prepent it with get_live_server_path
    to allow relative calls
    """

    from lxml.etree import XPathEvalError
    from lxml.html import document_fromstring

    from twill.errors import TwillException


    def visit_with_xpath(xpath):
        tree = document_fromstring(browser.get_html())

        try:
            result = tree.xpath(xpath)
        except XPathEvalError:
            raise TwillException("Bad xpath" % xpath)

        if len(result) == 0:
            raise TwillException("No match")
        elif len(result) > 1:
            raise TwillException("xpath returned multiple hits! Cannot visit.")

        if not result[0].get("href"):
            raise TwillException("xpath match do not have 'href' attribute")

        response = original_go(result[0].get("href"))
        if browser.result.get_http_code() == 500:
            raise extract_django_traceback(twill=browser)
        else:
            return response
    return visit_with_xpath

def mock_settings(settings_attribute, value):
    from django.conf import settings
    
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not hasattr(settings, settings_attribute):
                delete = True
            else:
                delete = False
                original_value = getattr(settings, settings_attribute)

            setattr(settings, settings_attribute, value)

            try:
                retval = f(*args, **kwargs)
            finally:
                if delete:
                    # could not delete directly as LazyObject does not implement
                    # __delattr__ properly
                    if settings._wrapped:
                        delattr(settings._wrapped, settings_attribute)
                else:
                    setattr(settings, settings_attribute, original_value)

            return retval
        return wrapped
    return wrapper

