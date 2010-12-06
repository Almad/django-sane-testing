Django: Sane Testing
========================

django-sane-testing integrates Django with Nose testing framework. Goal is to provide nose goodies to Django testing and to support feasible integration or functional testing of Django applications, for example by providing more control over transaction/database handling.

Thus, there is a way to start HTTP server for non-WSGI testing - like using Selenium or Windmill.

Selenium has also been made super easy - just start --with-selenium, inherit from SeleniumTestCase and use self.selenium.

Package is documented - see docs/ or http://readthedocs.org/projects/Almad/django-sane-testing/docs/index.html .
