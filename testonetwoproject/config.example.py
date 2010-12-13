
WINDMILL_BROWSER = 'firefox'

### Django settings


DEBUG = True
TEMPLATE_DEBUG = DEBUG


ADMINS = (
     # ('Almad', 'bugs at almad.net'),
)

URL_ROOT="http://localhost:8000/"

SITE_ID =1

MANAGERS = ADMINS

DATABASES = {
    'default' : {
        'ENGINE' : 'django.db.backends.sqlite3',
        'NAME' : "/tmp/dst.db",
        'TEST_NAME' : "/tmp/test_dst.db",
    },
    'users' : {
        'ENGINE' : 'django.db.backends.sqlite3',
        'NAME' : "/tmp/udst.db",
        'TEST_NAME' : "/tmp/test_udst.db",
    },
}

TIME_ZONE = 'Europe/Prague'

LANGUAGE_CODE = 'cs'
FILE_CHARSET = 'utf-8'
DEFAULT_CHARSET = 'utf-8'

USE_I18N = True

MEDIA_ROOT = "/home/almad/project/libkeykeeper/keykeeper/media/"
MEDIA_URL = "/media/"

ADMIN_MEDIA_PREFIX = "/adminmedia/"
SECRET_KEY = 'qjgj741513+cjj9lb+46&f3gyvh@0jgou-rx-tqbziw6f$bt59xxx!'
