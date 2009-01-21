from djangosanetesting.cases import UnitTestCase

class TestUnit(UnitTestCase):
    def test_simple_assert_methods_true(self):
        self.assert_true(True)
        # existence of alias
        self.assertTrue(True)
        assert self.assert_true == self.assertTrue
    
    def test_simple_assert_methods_true_false(self):
        self.assert_raises(AssertionError, lambda:self.assert_true(False))
    
    def test_simple_assert_methods_raises(self):
        pass
#        self.assert_raises(True)
#        self.assertTrue(True)

class TestUnitAliases(UnitTestCase):
    
    def get_camel(self, name):
        if name.startswith("_") or name.endswith("_"):
            raise ValueError(u"Cannot ransform to CamelCase world when name begins or ends with _")
        camel = list(name)
        while "_" in camel:
            index = camel.index("_")
            del camel[index]
            if camel[index] is "_":
                raise ValueError(u"Double underscores are not allowed")
            camel[index] = camel[index].upper()
        return ''.join(camel)
    
    def test_camelcase_aliases(self):
        for i in ["assert_true", "assert_equals", "assert_false", "assert_almost_equals"]:
            #FIXME: yield tests after #12 is resolved
            #yield lambda x, y: self.assert_equals, getattr(self, i), getattr(self, self.get_camel(i))
            self.assert_equals(getattr(self, i), getattr(self, self.get_camel(i)))
    
    def test_get_camel(self):
        self.assert_equals("assertTrue", self.get_camel("assert_true"))
    
    def test_get_camel_invalid_trail(self):
        self.assert_raises(ValueError, lambda:self.get_camel("some_trailing_test_"))

    def test_get_camel_invalid_double_under(self):
        self.assert_raises(ValueError, lambda:self.get_camel("toomuchtrail__between"))
                           
    def test_get_camel_invalid_prefix(self):
        self.assert_raises(ValueError, lambda:self.get_camel("_prefix"))

class TestProperClashing(UnitTestCase):
    """ TODO: test we're getting expected failures when working with db"""
