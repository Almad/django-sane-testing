import os
from django.conf import settings

DEFAULT_LIVE_SERVER_PROTOCOL = "http"
DEFAULT_LIVE_SERVER_PORT = 8000
DEFAULT_LIVE_SERVER_ADDRESS = '0.0.0.0'
DEFAULT_URL_ROOT_SERVER_ADDRESS = 'localhost'

def is_test_database():
    """
    Return whether we're using test database. Can be used to determine if we're
    running tests.
    """

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

    try:
        if settings.DATABASE_ENGINE == 'sqlite3':
            if not os.path.exists(settings.DATABASE_NAME):
                raise DatabaseError()
        connection.cursor()
        return True
    except DatabaseError, err:
        return False

def get_live_server_path():

    return getattr(settings, "URL_ROOT", "%s://%s:%s/" % (
        getattr(settings, "LIVE_SERVER_PROTOCOL", DEFAULT_LIVE_SERVER_PROTOCOL),
        getattr(settings, "URL_ROOT_SERVER_ADDRESS", DEFAULT_URL_ROOT_SERVER_ADDRESS),
        getattr(settings, "LIVE_SERVER_PORT", DEFAULT_LIVE_SERVER_PORT)
    ))

def twill_patched_go(original_go):
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
        return original_go(uri, *args, **kwargs)

    return twill_go_with_relative_paths

def mock_settings(settings_attribute, value):
    def wrapper(f):
        def wrapped(*args, **kwargs):
            if hasattr(settings, settings_attribute):
                delete = True
            else:
                delete = False
                original_value = getattr(settings, settings_attribute)

            setattr(settings, settings_attribute, value)

            retval = f(*args, **kwargs)

            if delete:
                delattr(settings, settings_attribute)
            else:
                setattr(settings, settings_attribute, original_value)

            return retval
        return wrapped
    return wrapper

