import sys

from noseplugins import LiveHttpServerRunnerPlugin, DjangoPlugin

from django.conf import settings

import nose
from nose.config import Config, all_config_files
from nose.plugins.manager import DefaultPluginManager

def run_tests(test_labels, verbosity=1, interactive=True, extra_tests=[]):
    """ Run tests with nose instead of defualt test runner """
    # we have to strip script name before passing to nose
#    sys.argv = argv_backup[0:1]
    config = Config(files=all_config_files(), plugins=DefaultPluginManager([LiveHttpServerRunnerPlugin(), DjangoPlugin()]))
    
    # activate all required plugins
    if DjangoPlugin.activation_parameter not in sys.argv:
        sys.argv.append(DjangoPlugin.activation_parameter)

    if LiveHttpServerRunnerPlugin.activation_parameter not in sys.argv:
        sys.argv.append(LiveHttpServerRunnerPlugin.activation_parameter)

    return nose.run(config=config)
    #TODO: return len(result.failures) + len(result.errors)

run_tests.__test__ = False

