from djangosanetesting.cases import TemplateTagTestCase

class TestTagLib(TemplateTagTestCase):
    preload = ('dsttesttags',)

    def test_tag_error(self):
        self.assert_raises(self.TemplateSyntaxError, self.render_template,
                           '{% table %}')

    def test_tag_output(self):
        self.assert_equal(self.render_template('{% table x_y z %}'),
            u'<table><tr><td>x</td><td>y</td></tr><tr><td>z</td></tr></table>')

class TestFilterLib(TemplateTagTestCase):
    preload = ('dsttestfilters',)

    def test_filter_output(self):
        self.assert_equal(self.render_template('{{ a|ihatebs }}', a='abc'),
                         u'aac')

class TestBoth(TestTagLib, TestFilterLib):
    preload = ('dsttesttags', 'dsttestfilters')

    def _call_test_render(self):
        return self.render_template('{% table b %}{{ a|ihatebs }}',
                                     a='a_bb_d b')

    def test_both_output(self):
        self.assert_equal(self._call_test_render(), u'<table><tr><td>b</td></tr>'
                         '</table>a_aa_d a')

    def test_preload_none(self):
        self.preload = ()
        self.assert_raises(self.TemplateSyntaxError, self._call_test_render)

    def test_preload_tags_only(self):
        self.preload = ('dsttesttags',)
        self.assert_raises(self.TemplateSyntaxError, self._call_test_render)

    def test_preload_filters_only(self):
        self.preload = ('dsttestfilters',)
        self.assert_raises(self.TemplateSyntaxError, self._call_test_render)

class TestMisc(TemplateTagTestCase):
    def test_context(self):
        self.assert_equal(self.render_template('{{ cvar }}'), u'')
        self.assert_equal(self.render_template('{{ cvar }}', cvar=123), u'123')

    def test_nonexistent_taglib(self):
        self.preload = ('nonexistent',)
        self.assert_raises(self.TemplateSyntaxError, self.render_template,
                           'sthing')
