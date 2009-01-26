.. _intro:

====================
Introduction
====================

Django: Sane Testing is a `Python`_ library for `Django`_ framework that makes it possible to test.

As much as I like some `Django`_ concepts and as much as authors embrace testing in official documentation, I doubt that anyone really tried them in detail. Some basic testing techniques are impossible with `Django`_ and this library comes to fix them.

One of the great flaws is very simplistic testing system. By it's nature it's very slow (flushing database when not needed [#fTrans]_), it does not allow some basic xUnit features and also do not allow testing via HTTP [#fLiveServer]_ and provides to extensibility model to fix the issues.

However, there is an excellent option available. `Nose`_ library is excellent test-dicovery framework, backward-compatible with PyUnit, that provides nice plugin interface to hook your own stuff. To make my life simpler, most of this library is made as a `nose`_ plugin.

And don't be afraid, we have TEST_RUNNER too, so your ``./manage.py test`` will still work.

--------------------
Feature overview
--------------------

Library supports following:

* Nose integration (load plugins and try ``noserun``)
* `Django`_ integration (``./manage.py test`` and boo ya)
* True unittests (no database interaction, no handling needed = SPEED)
* HTTP tests (You can test with `urllib2 <http://docs.python.org/library/urllib2.html>`_)
* Transactional database tests (everything in one transaction, no database flush)
* `Selenium`_ RC integration (our pages needs to be tested with browser)
* `CherryPy`_ can be used instead of `Django`_ 's WSGI (when you need usable server	)

.. _Python: http://www.python.org/
.. _Django: http://www.djangoproject.com/
.. _Nose: http://somethingaboutorange.com/mrl/projects/nose/
.. _Django ticket #3357: http://code.djangoproject.com/ticket/3357
.. _Selenium: http://seleniumhq.org/
.. _CherryPy: http://www.cherrypy.org/


.. rubric:: Footnotes

.. [#fTrans] At least transactional test cases are going to be implemented in Django 1.1, see `#8138 <http://code.djangoproject.com/ticket/8138>`_.
.. [#fLiveServer] Kinda buggy when we're talking about HTTP framework. See `#2879 <http://code.djangoproject.com/ticket/2879>`_.