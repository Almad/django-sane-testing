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

Easiest way to run tests is to put *TEST_RUNNER='djangosanetesting.testrunner.run_tests'* into your :file:`settings.py`. This still allows you to select individual tests by running ``./manage.py test testpackage.module.module:Class.method``, however there is no way to disable some tests (by not using some plugin) or to use additional nose plugins.

More flexible and granular way is using standard ``nosetests`` command. However, keep in mind:

* There is no path handling done for you
* DJANGO_SETTINGS_VARIABLE is also not set by default

Most likely, you'll end up with something like ``DJANGO_SETTINGS_MODULE="settings" PYTHONPATH=".:.." nosetests --with-django``; you can, however, flexibly add another nose modules (like ``--with-coverage``).

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

:class:`DjangoPlugin` takes care about basic Django environment setup. It **must** be loaded in order to use other plugins with Django (obviously). This plugin takes care about :class:`DatabaseTestCase` and :class:`DestructiveDatabaseTestCase`:

* If :attr:`no_database_interaction` attribute is True, then whole database handling is skipped (this is to speed thing up for :class:`UnitTestCase`)
* If :attr:`database_single_transaction` is True (:class:`DatabaseTestCase`), manual transaction handling is enabled and things are rolled back after every case.
* If :attr:`database_flush` is True, then database if flushed before every case (and on the beginning of next one, if needed)

.. _django-live-server-plugin:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:class:`DjangoLiveServerPlugin`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Responsible for starting HTTP server, sort of same as ``./manage.py runserver``, however testing server is multithreaded (as if with patch from `#3357 <http://code.djangoproject.com/ticket/3357>`_, but always enabled: if you'll any problems with it, write me).

Server is first started when :attr:`start_live_server` attribute is first encountered, and is stopped after whole testsuite.

.. Warning::

  Because application logic is always executed in another thread (even when server would be single-threaded), it's not possible to use :class:`HttpTestCase`'s with in-memory databases (well, theoretically, we could do database setup in each thread and have separate databases, but that will be really nasty).

  Thus, if encountered with in-memory database, server is not started and :exc:`SkipTest` is raised instead.

.. _cherrypy-live-server-plugin:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:class:`CherryPyLiveServerPlugin`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Responsible for starting HTTP server, in similar way to :class:`DjangoLiveServerPlugin`. However, `CherryPy`_ WSGI is used instead, as it's much more mature and considered to be production-ready, unlike Django's development server.

Use when in need of massive parallel requests, or when encountering a bug (like `#10117 <http://code.djangoproject.com/ticket/10117>`_).

.. Note::
  When using ``./manage.py test``, Django server is used by default. You can use `CherryPy`_'s by setting ``CHERRYPY_TEST_SERVER = True`` in settings.py.

.. Warning::
  :class:`DjangoLiveServerPlugin` (``--with-djangoliveserver``) and :class:`CherryPyLiveServerPlugin` (``--with-cherrypyliveserver``) are mutually exclusive. Using both will cause errors, and You're responsible for choosing one when running tests with ``nosetests`` (see :ref:`running-tests` for details).

.. _selenium-plugin:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:class:`SeleniumPlugin`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`Selenium`_ is excellent tool for regression (web application) testing. :class:`SeleniumPlugin` easily allows you to use xUnit infrastructure together with `Selenium RC`_ and enjoy unified, integrated infrastructure.

Selenium proxy server must be set up and running, there is no support for auto-launching (yet).

:class:`SeleniumPlugin` recognizes following configuration variables in settings.py:

* ``SELENIUM_BROWSER_COMMAND`` - which browser command should be send to proxy server to launch. Default to "*opera" and may require some more complicated adjusting on some configurations, take a look at `experimental launchers <http://seleniumhq.org/projects/remote-control/experimental.html>`_.
* ``SELENIUM_HOST`` - where Selenium proxy server is running. Default to "localhost"
* ``SELENIUM_PORT`` - to which port Selenium server is bound to. Default to 4444.
* ``SELENIUM_URL_ROOT`` - where is (from proxy server's point of view) application running. Default to "http://localhost:8000/".
* ``FORCE_SELENIUM_TESTS`` changes running behavior, see below.

When plugin encounters ``selenium_start`` attribute (set to True), it tries to start browser on selenium proxy. If exception occurs (well, I'd catch socket errors, but this seems to be impossible on Windows), it assumes that proxy is not running, thus environment conditions are not met and :exc:`SkipTest` is raised. If ``FORCE_SELENIUM_TESTS`` is set to True, then original exceptin is raised instead, causing test to fail (usable on web testing CI server to ensure tests are runnig properly and are not mistakenly skipped).


.. _django-sane-testing: http://devel.almad.net/trac/django-sane-testing/
.. _Selenium: http://seleniumhq.org/
.. _Selenium RC: http://seleniumhq.org/projects/remote-control/
.. _CherryPy: http://www.cherrypy.org/
