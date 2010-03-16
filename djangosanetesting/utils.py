from django.conf import settings

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
