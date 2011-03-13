#!/usr/bin/env python2

from paver.easy import *
from paver.setuputils import setup

VERSION = '0.5.10'
name = 'djangosanetesting'

setup(
    name = name,
    version = VERSION,
    url = 'http://devel.almad.net/trac/django-sane-testing/',
    author = 'Lukas Linhart',
    author_email = 'bugs@almad.net',
    description = 'Integrate Django with nose, Selenium, Twill and more. ''',
    long_description = u'''
======================
Django: Sane testing
======================

django-sane-testing integrates Django with Nose testing framework. Goal is to provide nose goodies to Django testing and to support feasible integration or functional testing of Django applications, for example by providing more control over transaction/database handling.

Thus, there is a way to start HTTP server for non-WSGI testing - like using Selenium or Windmill.

Selenium has also been made super easy - just start --with-selenium, inherit from SeleniumTestCase and use self.selenium.

Package is documented - see docs/ or http://readthedocs.org/projects/Almad/django-sane-testing/docs/index.html .
''',
    packages = ['djangosanetesting', 'djangosanetesting.selenium'],
    requires = ['Django (>=1.1)', 'nose (>=0.10)'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points = {
        'nose.plugins.0.10': [
            'djangoliveserver = %s.noseplugins:DjangoLiveServerPlugin' % name,
            'cherrypyliveserver = %s.noseplugins:CherryPyLiveServerPlugin' % name,
            'django = %s.noseplugins:DjangoPlugin' % name,
            'selenium = %s.noseplugins:SeleniumPlugin' % name,
            'sanetestselection = %s.noseplugins:SaneTestSelectionPlugin' % name,
            'djangotranslations = %s.noseplugins:DjangoTranslationPlugin' % name,
	    'djangoresultplugin = %s.noseplugins:ResultPlugin' % name,
        ]
    }
)

options(
    sphinx=Bunch(
        builddir="build",
        sourcedir="source"
    ),
    virtualenv=Bunch(
        packages_to_install=["nose", "Django>=1.1"],
        install_paver=False,
        script_name='bootstrap.py',
        paver_command_line=None,
        dest_dir="virtualenv"
    ),
)

@task
@consume_args
def unit(args, nose_run_kwargs=None):
    """ Run unittests """
    import os, sys
    from os.path import join, dirname, abspath
    
    test_project_module = "testproject"
    
    sys.path.insert(0, abspath(join(dirname(__file__), test_project_module)))
    sys.path.insert(0, abspath(dirname(__file__)))
    
    os.environ['DJANGO_SETTINGS_MODULE'] = "%s.settings" % test_project_module
    
    import nose

    os.chdir(test_project_module)

    argv = ["--with-django", "--with-cherrypyliveserver", "--with-selenium"] + args

    nose_run_kwargs = nose_run_kwargs or {}

    nose.run_exit(
        argv = ["nosetests"] + argv,
        defaultTest = test_project_module,
        **nose_run_kwargs
    )
