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

However, you are not *required* to inherit from those (except for :ref:`twill <twill-integration>`), althrough it's much advised to keep test cases intent-revealing. Job of the library is to:

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
* :class:`HttpTestCase` provides all goodies except Selenium. When first encountered, live server is spawned; after that, it's as fast as :class:`DestructiveDatabaseTestCase`.
* :class:`SeleniumTestCase` has it all (except speed).


.. _running-tests:

---------------------------
Running tests
---------------------------

Easiest way to run tests is to put ``TEST_RUNNER="djangosanetesting.testrunner.run_tests"`` into your :file:`settings.py`. This still allows you to select individual tests by running ``./manage.py test testpackage.module.module:Class.method``, however there is no way to disable some tests (by not using some plugin) or to use additional nose plugins.

More flexible and granular way is using standard ``nosetests`` command. However, keep in mind:

* There is no path handling done for you
* DJANGO_SETTINGS_VARIABLE is also not set by default

Most likely, you'll end up with something like ``DJANGO_SETTINGS_MODULE="settings" PYTHONPATH=".:.." nosetests --with-django``; you can, however, flexibly add another nose modules (like ``--with-coverage``).

Fine-grained test type selection is available via :class:`SaneTestSelectionPlugin`.

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
* :ref:`sane-test-selection-plugin`
* :ref:`django-translation-plugin`

.. _django-plugin:

^^^^^^^^^^^^^^^^^^^^^^^
:class:`DjangoPlugin`
^^^^^^^^^^^^^^^^^^^^^^^

:class:`DjangoPlugin` takes care about basic Django environment setup. It **must** be loaded in order to use other plugins with Django (obviously). This plugin takes care about :class:`DatabaseTestCase` and :class:`DestructiveDatabaseTestCase`:

* If :attr:`no_database_interaction` attribute is True, then whole database handling is skipped (this is to speed thing up for :class:`UnitTestCase`)
* If :attr:`database_single_transaction` is True (:class:`DatabaseTestCase`), manual transaction handling is enabled and things are rolled back after every case.
* If :attr:`database_flush` is True, then database if flushed before every case (and on the beginning of next one, if needed)

django.db.transaction is also available under self.transaction. Use at own discretion; you should only access it when using :class:`DestructiveDatabaseTestCase` (to make data available for server thread), messing with it when using :attr:`database_single_transaction` can cause test interaction.

Since 0.6, You can use ``--persist-test-database``. This is similar to quicktest command from django-test-utils: database is not flushed at the beginning if it exists and is not dropped at the end of the test run. Useful if You are debugging single test in flush-heavy applications.

.. Warning::

  By definition, strange things will happen if You'll change tests You're executing. Do not overuse this feature.

.. Warning::

  Tested by hand, not covered by automatic tests. Please report any bugs/testcases You'll encounter.


.. _django-live-server-plugin:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:class:`DjangoLiveServerPlugin`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Responsible for starting HTTP server, sort of same as ``./manage.py runserver``, however testing server is multithreaded (as if with patch from `#3357 <http://code.djangoproject.com/ticket/3357>`_, but always enabled: if you'll any problems with it, write me).

Server is first started when :attr:`start_live_server` attribute is first encountered, and is stopped after whole testsuite.

Plugin uses following setttings variables:
  * ``LIVE_SERVER_PORT`` - to which port live server is bound to. Default to 8000.
  * ``LIVE_SERVER_ADDRESS`` - to which IP address/interface server is bound to. Default to 0.0.0.0, meaning "all interfaces".


.. Warning::

  Because application logic is always executed in another thread (even when server would be single-threaded), it's not possible to use :class:`HttpTestCase`'s with in-memory databases (well, theoretically, we could do database setup in each thread and have separate databases, but that will be really nasty).

  Thus, if encountered with in-memory database, server is not started and :exc:`SkipTest` is raised instead.

.. Warning::

  Because of :ref:`twill integration <twill-integration>`, if non-empty :attr:`_twill` attribute is encountered, twill's reset_browser is called. This might be a problem if You, for whatever reason, set this attribute without interacting with it.

  If it annoys You, write me and I might do something better. Until then, it's at least documented.

.. _cherrypy-live-server-plugin:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:class:`CherryPyLiveServerPlugin`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Responsible for starting HTTP server, in similar way to :class:`DjangoLiveServerPlugin`. However, `CherryPy`_ WSGI is used instead, as it's much more mature and considered to be production-ready, unlike Django's development server.

Use when in need of massive parallel requests, or when encountering a bug (like `#10117 <http://code.djangoproject.com/ticket/10117>`_).

Plugin uses following setttings variables:
  * ``LIVE_SERVER_PORT`` - to which port live server is bound to. Default to 8000.
  * ``LIVE_SERVER_ADDRESS`` - to which IP address/interface server is bound to. Default to 0.0.0.0, meaning "all interfaces".

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
* ``SELENIUM_URL_ROOT`` - where is (from proxy server's point of view) application running. Default to "http://URL_ROOT_SERVER_ADDRESS:LIVE_SERVER_PORT/" (There is a difference between ``LIVE_SERVER_ADDRESS`` and ``URL_ROOT_SERVER_ADDRESS``, as ``LIVE_SERVER_ADDRESS`` is where server is bound to and ``URL_ROOT_SERVER_ADDRESS`` is which address is visible to client. Important when server is bound to all interfaces, as 0.0.0.0 is not a viable option for browser.)
* ``FORCE_SELENIUM_TESTS`` changes running behavior, see below.

When plugin encounters ``selenium_start`` attribute (set to True), it tries to start browser on selenium proxy. If exception occurs (well, I'd catch socket errors, but this seems to be impossible on Windows), it assumes that proxy is not running, thus environment conditions are not met and :exc:`SkipTest` is raised. If ``FORCE_SELENIUM_TESTS`` is set to True, then original exceptin is raised instead, causing test to fail (usable on web testing CI server to ensure tests are runnig properly and are not mistakenly skipped).

.. _sane-test-selection-plugin:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:class:`SaneTestSelectionPlugin`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Test cases varies in their speed, in order:

#. Unit tests
#. Database tests
#. Destructive database tests and HTTP tests
#. Selenium webtests

As your test suite will grow, you'll probably want to do *test pipelining*: run your tests in order, from fastest to slowest, and if one of the suites will break, you'll stop running slower tests to save time and resources.

This can be done with :class:`SaneTestSelectionPlugin`. When enabled by ``--with-sanetestselection``, you can pass additional parameters to enable respecitve types of tests:

* ``--select-unittests`` (or ``-u``)
* ``--select-databasetests``
* ``--select-destructivedatabasetests`` and ``--select-httptests``
* ``--select-seleniumtests``

Only selected test types will be run. Test type is determined from class attribute :attr:`test_type`; when not found, test is assumed to be unittest.

.. Note::
  You're still responsible for loading required plugins for respective test cases. Unlike test selection with usual plugins, selection plugin enables you to run slower tests without faster (i.e. HTTP tests without unittests), and also skipping is faster (Selection plugin is run before others, thus skip is done without any unneccessary database handling, which may not be true for usual skips).

.. _django-translation-plugin:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:class:`DjangoTranslationPlugin`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If :attr:`make_translation` is True (default for every test), django.utils.translation.activate() is called before every test. If :attr:`translation_language_code` is set, it's passed to activate(); otherwise settings.LANGUAGE_CODE or 'en-us' is used.

This allows you to use translatable string taking usage of ugettest_lazy in tests.

.. Warning::

    It looks like Django is not switching back to "null" translations once any translation has been selected. make_translations=False will thus return lastly-activated translation.

.. _syncdb-messing:

---------------------------
Messing with syncdb
---------------------------

You may be doing something irresponsible like, say, referencing :class:`ContentType` ID from fixtures, working around their dynamic creation by having own content type fixture. This, however, prevents you from specifying those in fixtures attribute, as flush emits post-sync signal causing ContentTypes to be created.

By specifying ``TEST_DATABASE_FLUSH_COMMAND``, you can reference a function for custom flushing (you can use resetdb instead).

.. Note::

    You must specify function object directly (it takes one argument, test_case object). Recognizing objects from string is not yet supported as it's not needed for me - patches and tests welcomed.

.. Note::

    When using django-sane-testing with south (in INSTALLED_APPS), You're now required to write You own command that will call both "syncdb" and "migrate". Sane-testing will have one for future releases.

Also, create_test_db (which is needed to be run at the very beginning) emits post_sync signal. Thus, you also probably want to set ``FLUSH_TEST_DATABASE_AFTER_INITIAL_SYNCDB`` to True.

.. _twill-integration:

------------------
Twill integration
------------------

`Twill`_ is simple browser-like library for page browsing and tests. For :class:`HttpTestCase` and all inherited TestCases, :attr:`self.twill` is available with twill's ``get_browser()``. It's setted up lazily and is resetted and purged after test case.

Browser has patched :attr:`go()` method: You can pass relative paths to it.

.. Note::

  Twill is using standard HTTP instead of WSGI intercept. This might be available in the future as an option, if there is a demand or patch written.

.. _django-sane-testing: http://devel.almad.net/trac/django-sane-testing/
.. _Selenium: http://seleniumhq.org/
.. _Selenium RC: http://seleniumhq.org/projects/remote-control/
.. _CherryPy: http://www.cherrypy.org/
.. _Twill: http://twill.idyll.org/

