#!/usr/bin/env python

try:
    import ez_setup
    ez_setup.use_setuptools()
except ImportError:
    pass

from setuptools import setup

project_dir = 'djangosanetesting'
name = 'djangosanetesting'

version = __import__('djangosanetesting').__versionstr__
setup(
    name = name, 
    version = version,
    url = 'http://devel.almad.net/trac/django-sane-testing/',
    author = 'Lukas Linhart',
    author_email = 'bugs@almad.net',
    description = 'Support sane testing in django using nose.',
    packages = ['djangosanetesting'],
    scripts = [],
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
            'djangoliveserver = %s.noseplugins:LiveHttpServerRunnerPlugin' % name,
            'django = %s.noseplugins:DjangoPlugin' % name,
        ]
    }
)
