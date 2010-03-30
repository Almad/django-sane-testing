"""
Utility methods for cache clear.
Used to somehow partially backport http://code.djangoproject.com/ticket/12671
to Django < 1.2
"""

from django.core.cache import cache
from django.db import connection

import shutil

###### clear functions

def clear_db(cache):
    cursor = connection.cursor()
    cursor.execute('DELETE FROM %s' % cache._table)

def clear_filebased(cache):
    try:
        shutil.rmtree(cache._dir)
    except (IOError, OSError):
        pass

def clear_memcached(cache):
    cache._cache.flush_all()

def clear_locmem(cache):
    cache._cache.clear()
    cache._expire_info.clear()

###### end of clear functions


# map

BACKEND_CLEAR_MAP = {
    'db' : clear_db,
    'dummy' : lambda x: x,
    'filebased' : clear_filebased,
    'memcached' : clear_memcached,
    'locmem' : clear_locmem,
}

# utility methods

def get_cache_class():
    return ''

def flush_django_cache():
    try:
        cache.clear()
    except AttributeError:
        # Django < 1.2, backports
        backend_name = cache.__module__.split(".")[-1:][0]
        
        if backend_name not in BACKEND_CLEAR_MAP:
            raise ValueError("Don't know how to clear cache for %s backend" % backend_name)

        BACKEND_CLEAR_MAP[backend_name](cache)
