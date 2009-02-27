import urllib2

from djangosanetesting.cases import DatabaseTestCase, HttpTestCase

from testapp.models import ExampleModel

 
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
    
    def test_client_available(self):
        res = self.client.get('/testtwohundred/')
        self.assert_equals(200, res.status_code)

class TestProperClashing(DatabaseTestCase):
    """
    Test we're getting expected failures when working with db,
    i.e. that database is not purged between tests, only rolled back.
    We rely that test suite executed methods in this order:
      (1) test_aaa_commit_object
      (2) test_bbb_object_present
      (3) test_ccc_object_still_present
      
    This is antipattern and should not be used, but it's hard to test
    framework from within ;) Better solution would be greatly appreciated.  
    """
    
    def test_aaa_commit_object(self):
        ExampleModel.objects.create(name="test1")
        self.transaction.commit()

    def test_bbb_object_present(self):
        self.assert_equals(1, len(ExampleModel.objects.all()))

    def test_ccc_object_still_present(self):
        self.assert_equals(1, len(ExampleModel.objects.all()))
        ExampleModel.objects.all()[0].delete()
        self.transaction.commit()


class TestFixturesLoadedProperly(HttpTestCase):
    fixtures = ["random_model_for_testing"]

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        # I did not found how to load those variables from django.conf.settings,
        # so I must just hardcode them. Advices welcomed.
        self.host = 'localhost'
        self.port = 8000
    
    def test_model_loaded(self):
        self.assert_equals(2, len(ExampleModel.objects.all()))

    def test_available_in_another_thread(self):
        self.assertEquals(u'200 OK', urllib2.urlopen('http://%(host)s:%(port)s/assert_two_example_models/' % {
            'host' : self.host,
            'port' : self.port
        }).read())
