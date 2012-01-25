
__version__ = (0, 5, 11, '')
__versionstr__ = '0.5.11'

try:
    from django.db import DEFAULT_DB_ALIAS
    MULTIDB_SUPPORT = True
except ImportError:
    DEFAULT_DB_ALIAS = 'default'
    MULTIDB_SUPPORT = False

from djangosanetesting.cases import *
from djangosanetesting.testrunner import *
