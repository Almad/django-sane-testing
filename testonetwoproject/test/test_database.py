import urllib2

from djangosanetesting.cases import DatabaseTestCase, DestructiveDatabaseTestCase, HttpTestCase
from djangosanetesting.utils import mock_settings

from testapp.models import ExampleModel

import django

class TestDjangoOneTwoMultipleDatabases(DestructiveDatabaseTestCase):
    """
    Test we're flushing multiple databases
    i.e. that all databases are flushed between tests

    We rely on fact that cases are invoked after each other, which is bad :-]

    This is antipattern and should not be used, but it's hard to test
    framework from within :-] Better solution would be greatly appreciated.
    """
    multi_db = True

    def setUp(self):
        super(TestDjangoOneTwoMultipleDatabases, self).setUp()

        if django.VERSION[0] < 1 or (django.VERSION[0] == 1 and django.VERSION[1] < 2):
            raise self.SkipTest("This case is only for Django 1.2+")

    def test_aaa_multiple_databases_flushed(self):
        self.assert_equals(0, ExampleModel.objects.count())
        self.assert_equals(0, ExampleModel.objects.using('users').count())

        ExampleModel.objects.create(name="test1")
        ExampleModel.objects.using('users').create(name="test1")

        self.transaction.commit()
        self.transaction.commit(using='users')

        self.assert_equals(1, ExampleModel.objects.count())
        self.assert_equals(1, ExampleModel.objects.using('users').count())

    def test_bbb_multiple_databases_flushed(self):
        self.assert_equals(0, ExampleModel.objects.count())
        self.assert_equals(0, ExampleModel.objects.using('users').count())

        ExampleModel.objects.create(name="test1")
        ExampleModel.objects.using('users').create(name="test1")

        self.transaction.commit()
        self.transaction.commit(using='users')

        self.assert_equals(1, ExampleModel.objects.count())
        self.assert_equals(1, ExampleModel.objects.using('users').count())
