from djangosanetesting.cases import UnitTestCase

class TestUnit(UnitTestCase):
    def test_just_were_discovered(self):
        pass

class TestProperClashing(UnitTestCase):
    """ TODO: test we're getting expected failures when working with db"""