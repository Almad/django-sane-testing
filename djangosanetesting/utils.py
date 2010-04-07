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

def get_live_server_path():

    return getattr(settings, "URL_ROOT", "%s://%s:%s/" % (
        getattr(settings, "LIVE_SERVER_PROTOCOL", DEFAULT_LIVE_SERVER_PROTOCOL),
        getattr(settings, "URL_ROOT_SERVER_ADDRESS", DEFAULT_URL_ROOT_SERVER_ADDRESS),
        getattr(settings, "LIVE_SERVER_PORT", DEFAULT_LIVE_SERVER_PORT)
    ))
