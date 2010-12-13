# -*- coding: utf-8 -*-

from os import path

working_dir = path.dirname(path.abspath(__file__))

APPLICATION_ROOT=path.join(path.dirname(path.abspath(__file__)))

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    'django.template.loaders.eggs.load_template_source',
)

# AUTHENTICATION_BACKENDS = ('keykeeper.libopenid.OpenidBackend',)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
#    'django.contrib.sessions.middleware.SessionMiddleware',
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.middleware.transaction.TransactionMiddleware',
#    'django.middleware.http.SetRemoteAddrFromForwardedFor',
)

ROOT_URLCONF = 'testproject.urls'

SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_NAME = 'testproject_id'

TEMPLATE_DIRS = (
    path.join(APPLICATION_ROOT, 'template/')
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'testapp',
)

TEST_RUNNER='djangosanetesting.testrunner.run_tests'

TEST_DATABASE_CHARSET="utf8"

CHERRYPY_TEST_SERVER = True

LANGUAGE_CODE = 'cs'

CACHE_BACKEND = 'locmem://'

DST_FLUSH_DJANGO_CACHE = True
NONSENSICAL_SETTING_ATTRIBUTE_FOR_MOCK_TESTING = "owned"

DEBUG = True

from config import *

