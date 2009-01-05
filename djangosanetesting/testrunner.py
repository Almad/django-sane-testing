import sys

from noseplugins import LiveHttpServerRunnerPlugin

from django.conf import settings
from django.core.management import setup_environ
from django.test.utils import setup_test_environment, teardown_test_environment

import nose
from nose.config import Config, all_config_files
from nose.plugins.manager import DefaultPluginManager

def run_tests(test_labels, verbosity=1, interactive=True, extra_tests=[]):
    """ Run tests with nose instead of defualt test runner """
    setup_test_environment()

    from django.db import connection
    old_name = settings.DATABASE_NAME
    connection.creation.create_test_db(verbosity, autoclobber=not interactive)
    argv_backup = sys.argv

    # we have to strip script name before passing to nose
    sys.argv = argv_backup[0:1]
    config = Config(files=all_config_files(), plugins=DefaultPluginManager([LiveHttpServerRunnerPlugin()]))

    nose.run(config=config)

    sys.argv = argv_backup
    connection.creation.destroy_test_db(old_name, verbosity)
    teardown_test_environment()

    #TODO: return len(result.failures) + len(result.errors)

run_tests.__test__ = False

