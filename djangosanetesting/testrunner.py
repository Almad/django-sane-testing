import sys

from djangosanetesting.noseplugins import LiveHttpServerRunnerPlugin, DjangoPlugin, SeleniumPlugin

from django.conf import settings

import nose
from nose.config import Config, all_config_files
from nose.plugins.manager import DefaultPluginManager

def activate_plugin(plugin):
    if plugin.activation_parameter not in sys.argv:
        sys.argv.append(plugin.activation_parameter)

def run_tests(test_labels, verbosity=1, interactive=True, extra_tests=[]):
    """ Run tests with nose instead of defualt test runner """
    # we have to strip script name before passing to nose
#    sys.argv = argv_backup[0:1]
    config = Config(files=all_config_files(), plugins=DefaultPluginManager([LiveHttpServerRunnerPlugin(), DjangoPlugin(), SeleniumPlugin()]))
    
    # activate all required plugins
    activate_plugin(DjangoPlugin)
    activate_plugin(LiveHttpServerRunnerPlugin)
    activate_plugin(SeleniumPlugin)

    return nose.run(config=config)

run_tests.__test__ = False

