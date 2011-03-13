import os
import sys

import nose
from nose.config import Config, all_config_files
from nose.plugins.manager import DefaultPluginManager

from django.core.management.base import BaseCommand
from django.test import utils

from djangosanetesting.noseplugins import (
    DjangoPlugin,
    DjangoLiveServerPlugin, SeleniumPlugin, CherryPyLiveServerPlugin,
    DjangoTranslationPlugin,
    ResultPlugin,
)

__all__ = ("run_tests",)

"""
Act as Django test runner, but use nose. Enable common django-sane-testing
plugins by default.

You can use

    DST_NOSE_ARGS = ['list', 'of', 'args']

in settings.py for arguments that you always want passed to nose.

Test runners themselves are basically copypasted from django-nose project.
(C) Jeff Balogh and contributors, released under BSD license.

Thanks and kudos.

Modified for django-sane-testing by Almad.
"""

def activate_plugin(plugin, argv=None):
    argv = argv or sys.argv
    if plugin.activation_parameter not in argv:
        argv.append(plugin.activation_parameter)

try:
    any
except NameError:
    def any(iterable):
        for element in iterable:
            if element:
                return True
        return False

def run_tests(test_labels, verbosity=1, interactive=True, spatial_db=False):
    """Test runner that invokes nose."""
    # Prepare django for testing.
    from django.conf import settings

    utils.setup_test_environment()
    old_db_name = settings.DATABASE_NAME

    result_plugin = ResultPlugin()
    plugins = [DjangoPlugin(), SeleniumPlugin(), DjangoTranslationPlugin(), result_plugin]
    
    if getattr(settings, 'CHERRYPY_TEST_SERVER', False):
        plugins.append(CherryPyLiveServerPlugin())
    else:
        plugins.append(DjangoLiveServerPlugin())
    
    # Do not pretend it's a production environment.
    # settings.DEBUG = False

    # We pass nose a list of arguments that looks like sys.argv, but customize
    # to avoid unknown django arguments.
    nose_argv = ['nosetests']
    if hasattr(settings, 'NOSE_ARGS'):
        nose_argv.extend(settings.NOSE_ARGS)

    # activate all required plugins
    activate_plugin(DjangoPlugin, nose_argv)
    activate_plugin(SeleniumPlugin, nose_argv)
    activate_plugin(DjangoTranslationPlugin, nose_argv)
#    activate_plugin(ResultPlugin, nose_argv)

    if getattr(settings, 'CHERRYPY_TEST_SERVER', False):
        activate_plugin(CherryPyLiveServerPlugin, nose_argv)
    else:
        activate_plugin(DjangoLiveServerPlugin, nose_argv)

    # Skip over 'manage.py test' and any arguments handled by django.
    django_opts = ['--noinput']
    for opt in BaseCommand.option_list:
        django_opts.extend(opt._long_opts)
        django_opts.extend(opt._short_opts)

    nose_argv.extend(opt for opt in sys.argv[2:] if
                     not any(opt.startswith(d) for d in django_opts))

    if verbosity >= 1:
        print ' '.join(nose_argv)

    test_program = nose.core.TestProgram(argv=nose_argv, exit=False,
                                                addplugins=plugins)
    
    # FIXME: ResultPlugin is working not exactly as advertised in django-nose
    # multiple instance problem, find workaround
#    result = result_plugin.result
#    return len(result.failures) + len(result.errors)
    return not test_program.success

def _get_options():
    """Return all nose options that don't conflict with django options."""
    cfg_files = nose.core.all_config_files()
    manager = nose.core.DefaultPluginManager()
    config = nose.core.Config(env=os.environ, files=cfg_files, plugins=manager)
    options = config.getParser().option_list
    django_opts = [opt.dest for opt in BaseCommand.option_list] + ['version']
    return tuple(o for o in options if o.dest not in django_opts and
                                       o.action != 'help')


# Replace the builtin command options with the merged django/nose options.
run_tests.options = _get_options()

run_tests.__test__ = False

