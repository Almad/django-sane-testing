#!/usr/bin/env python

try:
    import ez_setup
    ez_setup.use_setuptools()
except ImportError:
    pass

from setuptools import setup

project_dir = 'djangosanetesting'
name = 'djangosanetesting'

version = '0.5.3'
setup(
    name = name, 
    version = version,
    url = 'http://devel.almad.net/trac/django-sane-testing/',
    author = 'Lukas Linhart',
    author_email = 'bugs@almad.net',
    description = 'Support sane testing in django using nose.',
    packages = ['djangosanetesting', 'djangosanetesting.selenium'],
    scripts = [],
    install_requires = ['Django>=1.0_final','nose>=0.10'],
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
        ]
    }
)
