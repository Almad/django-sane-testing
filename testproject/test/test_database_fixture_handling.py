"""
Test that DatabaseTestCases has properly handled fixtures,
i.e. database is flushed when fixtures are different.

This would normally be usual TestCase, but we need to check
inter-case behaviour, so we rely that those cases are executed
one after another.

This is kinda antipattern, mail me for better solution ;)

Covers #6
"""
from djangosanetesting.cases import DatabaseTestCase
from testapp.models import ExampleModel

class TestAAAFirstfixture(DatabaseTestCase):
    fixtures = ['random_model_for_testing']
    def test_fixture_loaded(self):
        self.assert_equals(ExampleModel, ExampleModel.objects.get(pk=1).__class__)
        self.assert_equals(ExampleModel, ExampleModel.objects.get(pk=2).__class__)
    
class TestBBBSecondFixture(DatabaseTestCase):
    fixtures = ['duplicate_model_for_testing']
    def test_fixture_loaded(self):
        self.assert_equals(ExampleModel, ExampleModel.objects.get(pk=3).__class__)
        self.assert_equals(ExampleModel, ExampleModel.objects.get(pk=4).__class__)
    
    def test_aaa_fixture_not_loaded(self):
        self.assert_raises(ExampleModel.DoesNotExist, lambda:ExampleModel.objects.get(pk=1).__class__)
        self.assert_raises(ExampleModel.DoesNotExist, lambda:ExampleModel.objects.get(pk=2).__class__)    
    
    