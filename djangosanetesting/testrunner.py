import os
import sys

import nose
from nose.config import Config, all_config_files
from nose.plugins.manager import DefaultPluginManager

from django.core.management.base import BaseCommand
try:
    from django.test.simple import DjangoTestSuiteRunner
except ImportError:
    from djangosanetesting.runnercompat import DjangoTestSuiteRunner

from djangosanetesting.noseplugins import (
    DjangoPlugin,
    DjangoLiveServerPlugin, SeleniumPlugin, CherryPyLiveServerPlugin,
    DjangoTranslationPlugin,
    ResultPlugin,
)

__all__ = ("DstNoseTestSuiteRunner",)

# This file doen't contain tests
__test__ = False

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

OPTION_TRANSLATION = {'--failfast': '-x'}

class DstNoseTestSuiteRunner(DjangoTestSuiteRunner):

    def run_suite(self, nose_argv=None):
        """Test runner that invokes nose."""
        # Prepare django for testing.
        from django.conf import settings
    
        from django.test import utils
        utils.setup_test_environment()
    
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

        for plugin in _get_plugins_from_settings():
            plugins_to_add.append(plugin)
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
    
        nose_argv.extend(OPTION_TRANSLATION.get(opt, opt)
                         for opt in sys.argv[1:]
                         if opt.startswith('-') and not any(opt.startswith(d) for d in django_opts))
    
        if self.verbosity >= 2:
            print ' '.join(nose_argv)
    
        test_program = nose.core.TestProgram(argv=nose_argv, exit=False,
                                                    addplugins=plugins)
        
        # FIXME: ResultPlugin is working not exactly as advertised in django-nose
        # multiple instance problem, find workaround
    #    result = result_plugin.result
    #    return len(result.failures) + len(result.errors)
        return not test_program.success

    def run_tests(self, test_labels, extra_tests=None):
        """
        Run the unit tests for all the test names in the provided list.

        Test names specified may be file or module names, and may optionally
        indicate the test case to run by separating the module or file name
        from the test case name with a colon. Filenames may be relative or
        absolute.  Examples:

        runner.run_tests('test.module')
        runner.run_tests('another.test:TestCase.test_method')
        runner.run_tests('a.test:TestCase')
        runner.run_tests('/path/to/test/file.py:test_function')

        Returns the number of tests that failed.
        """
        
        from django.conf import settings
        
        nose_argv = ['nosetests', '--verbosity', str(self.verbosity)] + list(test_labels)
        if hasattr(settings, 'NOSE_ARGS'):
            nose_argv.extend(settings.NOSE_ARGS)

        # Skip over 'manage.py test' and any arguments handled by django.
        django_opts = ['--noinput']
        for opt in BaseCommand.option_list:
            django_opts.extend(opt._long_opts)
            django_opts.extend(opt._short_opts)

        nose_argv.extend(OPTION_TRANSLATION.get(opt, opt)
                         for opt in sys.argv[1:]
                         if opt.startswith('-') and not any(opt.startswith(d) for d in django_opts))

        if self.verbosity >= 2:
            print ' '.join(nose_argv)

        result = self.run_suite(nose_argv)
        ### FIXME
        class SimpleResult(object): pass
        res = SimpleResult()
        res.failures = ['1'] if result else []
        res.errors = []
        # suite_result expects the suite as the first argument.  Fake it.
        return self.suite_result({}, res)


def _get_options():
    """Return all nose options that don't conflict with django options."""
    cfg_files = nose.core.all_config_files()
    manager = nose.core.DefaultPluginManager()
    config = nose.core.Config(env=os.environ, files=cfg_files, plugins=manager)
    options = config.getParser().option_list
    django_opts = [opt.dest for opt in BaseCommand.option_list] + ['version']
    return tuple(o for o in options if o.dest not in django_opts and
                                       o.action != 'help')

def _get_plugins_from_settings():
    from django.conf import settings
    if hasattr(settings, 'NOSE_PLUGINS'):
        for plg_path in settings.NOSE_PLUGINS:
            try:
                dot = plg_path.rindex('.')
            except ValueError:
                raise exceptions.ImproperlyConfigured(
                                    '%s isn\'t a Nose plugin module' % plg_path)
            p_mod, p_classname = plg_path[:dot], plg_path[dot+1:]
            try:
                mod = import_module(p_mod)
            except ImportError, e:
                raise exceptions.ImproperlyConfigured(
                        'Error importing Nose plugin module %s: "%s"' % (p_mod, e))
            try:
                p_class = getattr(mod, p_classname)
            except AttributeError:
                raise exceptions.ImproperlyConfigured(
                        'Nose plugin module "%s" does not define a "%s" class' % (
                                                                p_mod, p_classname))
            yield p_class()

# Replace the builtin command options with the merged django/nose options.
DstNoseTestSuiteRunner.options = _get_options()
DstNoseTestSuiteRunner.__test__ = False

def run_tests(test_labels, verbosity=1, interactive=True, failfast=False, extra_tests=None):
    test_runner = DstNoseTestSuiteRunner(verbosity=verbosity, interactive=interactive, failfast=failfast)
    return test_runner.run_tests(test_labels, extra_tests=extra_tests)
