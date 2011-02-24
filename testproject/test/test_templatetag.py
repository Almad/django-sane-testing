from djangosanetesting.cases import TemplateTagTestCase

class TestTagLib(TemplateTagTestCase):
    preload = ('dsttesttags',)

    def test_tag_error(self):
        self.assertRaisesRegexp(self.TemplateSyntaxError,
            r'Not enough arguments for \'table\'',
            self._render_template, '{% table %}')

    def test_tag_output(self):
        self.assertEqual(self._render_template('''{% table x_y z %}'''),
            u'<table><tr><td>x</td><td>y</td></tr><tr><td>z</td></tr></table>')

class TestFilterLib(TemplateTagTestCase):
    preload = ('filters',)

    def test_filter_output(self):
        self.assertEqual(self._render_template('{{ a|ihatebs }}', a='abc'),
                         u'aac')

class TestBoth(TestTagLib, TestFilterLib):
    preload = ('dsttesttags', 'dsttestfilters')

    def _call_render(self):
        return self._render_template('{% table b %}{{ a|ihatebs }}',
                                     a='a_bb_d b')

    def test_both_output(self):
        self.assertEqual(self._call_render(), u'<table><tr><td>b</td></tr>'
                         '</table>a_aa_d a')

    def test_preload_none(self):
        self.preload = ()
        self.assertRaisesRegexp(self.TemplateSyntaxError,
            r'Invalid block tag: \'table\'', self._call_render)

    def test_preload_tags_only(self):
        self.preload = ('dsttesttags',)
        self.assertRaisesRegexp(self.TemplateSyntaxError,
            r'Invalid filter: \'ihatebs\'', self._call_render)

    def test_preload_filters_only(self):
        self.preload = ('dsttestfilters',)
        self.assertRaisesRegexp(self.TemplateSyntaxError,
            r'Invalid block tag: \'table\'', self._call_render)

class TestMisc(TemplateTagTestCase):
    def test_context(self):
        self.assertEqual(self._render_template('{{ cvar }}'), u'')
        self.assertEqual(self._render_template('{{ cvar }}', cvar=123), u'123')

    def test_nonexistent_taglib(self):
        self.preload = ('nonexistent',)
        self.assertRaisesRegexp(self.TemplateSyntaxError,
                                r'\'nonexistent\' is not a valid tag library',
                                self._render_template, 'sthing')
