
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
    'default': {
        'NAME': 'main',
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME' : '/tmp/test_dst_main.db'
    },
    'users': {
        'NAME': 'user',
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME' : '/tmp/test_dst_user.db'
    }
}

#DATABASE_OPTIONS = {"init_command": "SET storage_engine=INNODB" } 


TIME_ZONE = 'Europe/Prague'

LANGUAGE_CODE = 'cs'
FILE_CHARSET = 'utf-8'
DEFAULT_CHARSET = 'utf-8'

USE_I18N = True

MEDIA_ROOT = "/home/almad/project/libkeykeeper/keykeeper/media/"
MEDIA_URL = "/media/"

ADMIN_MEDIA_PREFIX = "/adminmedia/"
SECRET_KEY = 'qjgj741513+cjj9lb+46&f3gyvh@0jgou-rx-tqbziw6f$bt59xxx!'
