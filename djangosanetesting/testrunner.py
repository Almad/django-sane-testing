import sys

from djangosanetesting.noseplugins import DjangoLiveServerPlugin, DjangoPlugin, SeleniumPlugin, CherryPyLiveServerPlugin

import nose
from nose.config import Config, all_config_files
from nose.plugins.manager import DefaultPluginManager

__all__ = ("run_tests",)

def activate_plugin(plugin):
    if plugin.activation_parameter not in sys.argv:
        sys.argv.append(plugin.activation_parameter)

def run_tests(test_labels, verbosity=1, interactive=True, extra_tests=[]):
    """ Run tests with nose instead of defualt test runner """
    from django.conf import settings
    
    plugins = [DjangoPlugin(), SeleniumPlugin()]
    
    if getattr(settings, 'CHERRYPY_TEST_SERVER', False):
        plugins.append(CherryPyLiveServerPlugin())
    else:
        plugins.append(DjangoLiveServerPlugin())
    
    config = Config(files=all_config_files(), plugins=DefaultPluginManager(plugins))
    
    # we've been called in form ./manage.py test. Test is however not a test location,
    # so strip it so we can get one
    sys.argv = [sys.argv[0]] + sys.argv[2:] 
    
    # activate all required plugins
    activate_plugin(DjangoPlugin)
    activate_plugin(SeleniumPlugin)

    if getattr(settings, 'CHERRYPY_TEST_SERVER', False):
        activate_plugin(CherryPyLiveServerPlugin)
    else:
        activate_plugin(DjangoLiveServerPlugin)

    return nose.run(config=config)

run_tests.__test__ = False

