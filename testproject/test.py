import urllib2

from djangosanetesting.cases import HttpTestCase, UnitTestCase, DatabaseTestCase

from testapp.models import ExampleModel

class TestUnit(UnitTestCase):
    def test_empty(self):
        pass

class TestLiveServerRunning(HttpTestCase):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        # I did not found how to load those variables from django.conf.settings,
        # so I must just hardcode them. Advices welcomed.
        self.host = 'localhost'
        self.port = 8000
    
    def get_ok(self):
        self.assertEquals(u'200 OK', urllib2.urlopen('http://%(host)s:%(port)s/testtwohundred/' % {
            'host' : self.host,
            'port' : self.port
        }).read())
    
    def test_http_retrievable(self):
        return self.get_ok()
    
    def test_http_retrievable_repeatedly(self):
        return self.get_ok()

class TestDatabaseRollbackCase(DatabaseTestCase):
    """
    Check we got proper rollback when trying to play with models.
    """
    def test_inserting_two(self):
        # guard assertion
        self.assert_equals(0, len(ExampleModel.objects.all()))
        ExampleModel.objects.create(name="test1")
        ExampleModel.objects.create(name="test2")

        # check we got stored properly
        self.assert_equals(2, len(ExampleModel.objects.all()))

    def test_inserting_two_again(self):
        # guard assertion, will fail if previous not rolled back properly
        self.assert_equals(0, len(ExampleModel.objects.all()))

        ExampleModel.objects.create(name="test3")
        ExampleModel.objects.create(name="test4")

        # check we got stored properly
        self.assert_equals(2, len(ExampleModel.objects.all()))
