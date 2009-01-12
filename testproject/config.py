
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

DATABASE_ENGINE = "sqlite3"
DATABASE_NAME = "/tmp/testproject.db"
TEST_DATABASE_NAME = "/tmp/test_testproject.db"
DATABASE_USER = ""
DATABASE_PASSWORD = ""
DATABASE_HOST = "localhost"
DATABASE_PORT = ''

#DATABASE_OPTIONS = {"init_command": "SET storage_engine=INNODB" } 


TIME_ZONE = 'Europe/Prague'

LANGUAGE_CODE = 'cs'
FILE_CHARSET = 'utf-8'
DEFAULT_CHARSET = 'utf-8'

USE_I18N = True

MEDIA_ROOT = "/tmp/media/"
MEDIA_URL = "/media/"

ADMIN_MEDIA_PREFIX = "/adminmedia/"
SECRET_KEY = 'qjgj741513+cjj9lb+46&f3gyvh@0jgou-rx-tqbziw6f$bt59xxx!'
