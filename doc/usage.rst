.. _usage:

====================
Usage
====================

This part explains how to use `django-sane-testing`_ to create a workable test suite. For test writers, most important part is :ref:`about creating tests <writing-tests>`, testers and CI admins may be more interested in :ref:`executing them <running-tests>`.

.. _writing-tests:

---------------------------
  Writing tests
---------------------------

Various test types were identified when taking look at :ref:`developer tests <developer-tests>`. Every test type has it's corresponding class in :mod:`djangosanetesting.cases`, namely:

.. _list-of-test-cases:

* :class:`UnitTestCase`
* :class:`DatabaseTestCase`
* :class:`DestructiveDatabaseTestCase`
* :class:`HttpTestCase`
* :class:`SeleniumTestCase`

However, you are not *required* to inherit from those, althrough it's much advised to keep test cases intent-revealing. Job of the library is to:

* Start manual transaction handling and roll it back after test
* Flush database
* Start live server frontend
* Setup selenium proxy

Those are done by :ref:`plugins <list-of-plugins>`, and they dermine their jobs by looking at class attributes, namely:

* :attr:`database_single_transaction`
* :attr:`database_flush`
* :attr:`start_live_server`
* :attr:`selenium_start`

All of those are booleans. Because class attributes are currently used to determine behaviour, nor doctest nor function tests are supported (they will not break things, but you'll get no goodies from library).

To support proper test selection and error-handling, tests also has class atribute :attr:`required_sane_plugins`, which specifies list of plugins (from :ref:`those available <list-of-plugins>`) that are required for this type of test; if it's not, test automatically skip itself.

Proper defaults are selected when using :ref:`library test cases <list-of-test-cases>`; however, if you have your own and complicated test inheritance model, you can integrate it on your own.

When writing tests, keep in mind limitations of the individual test cases to prevent interacting tests:

* :class:`UnitTestCase` should not interact with database or server frontend
* :class:`DatabaseTestCase` must run in one transaction and thus cannot be multithreaded and must not call commit
* :class:`DestructiveDatabaseTestCase` is slow and do not have live server available (cannot test using urllib2 and friends)

.. _running-tests:

---------------------------
Running tests
---------------------------

Easiest way to run tests is to put *TEST_RUNNER='djangosanetesting.testrunner.run_tests'* into your :file:`settings.py`. This still allows you to select individual tests by running :cmd:`./manage.py test testpackage.module.module:Class.method`, however there is no way to disable some tests (by not using some plugin) or to use additional nose plugins.

More flexible and granular way is using standard :cmd:`nosetests` command. However, keep in mind:

* There is no path handling done for you
* DJANGO_SETTINGS_VARIABLE is also not set by default

Most likely, you'll end up with something like :cmd:`DJANGO_SETTINGS_MODULE="settings" PYTHONPATH=".:.." nosetests --with-django`; you can, however, flexibly add another nose modules (like ``--with-coverage``).

#TODO: Test type selection is not supported yet (= run all selenium tests but do not run unittests et al). This is considered a bug and will be fixed in next releases.

.. _plugins:
-----------------
Plugins
-----------------

Provided plugins:

.. _list-of-plugins:

* :ref:`django-plugin`
* :ref:`django-live-server-plugin`
* :ref:`cherrypy-live-server-plugin`
* :ref:`selenium-plugin`

.. _django-plugin:

^^^^^^^^^^^^^^^^^^^^^^^
:class:`DjangoPlugin`
^^^^^^^^^^^^^^^^^^^^^^^

.. _django-live-server-plugin:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:class:`DjangoLiveServerPlugin`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _cherrypy-live-server-plugin:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:class:`CherryPyLiveServerPlugin`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _selenium-plugin:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:class:`SeleniumPlugin`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. _django-sane-testing: http://devel.almad.net/trac/django-sane-testing/
