from django.test.utils import setup_test_environment, teardown_test_environment
from django.db.backends.creation import create_test_db, destroy_test_db
import nose

def run_tests(test_labels, verbosity=1, interactive=True, extra_tests=[]):
    """ Run tests with nose instead of defualt test runner """
    setup_test_environment()
    old_name = settings.DATABASE_NAME
    create_test_db(verbosity, autoclobber=not interactive)
    argv_backup = sys.argv
    # we have to strip script name before passing to nose
    sys.argv = argv_backup[0:1]
    config = Config(files=all_config_files(), plugins=DefaultPluginManager())
    nose.run(config=config)
    sys.argv = argv_backup
    destroy_test_db(old_name, verbosity)
    teardown_test_environment()

run_tests.__test__ = False

