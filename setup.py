#!/usr/bin/env python

try:
    import ez_setup
    ez_setup.use_setuptools()
except ImportError:
    pass

from setuptools import setup

project_dir = 'djangosanetesting'
name = 'djangosanetesting'

version = '0.5.7'
setup(
    name = name,
    version = version,
    url = 'http://devel.almad.net/trac/django-sane-testing/',
    author = 'Lukas Linhart',
    author_email = 'bugs@almad.net',
    description = u'''
    Django: Sane testing
    ======================

    django-sane-testing integrates Django with Nose testing framework. Goal is to provide nose goodies to Django testing and to support feasible integration or functional testing of Django applications, for example by providing more control over transaction/database handling.
    Thus, there is a way to start HTTP server for non-WSGI testing - like using Selenium or Windmill.
    Selenium has also been made super easy - just start --with-selenium, inherit from SeleniumTestCase and use self.selenium.
    Package is documented - see docs/ or http://getthedocs.org/Almad/djangosanetesting.
    ''',
    packages = ['djangosanetesting', 'djangosanetesting.selenium'],
    scripts = [],
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
        ]
    }
)
