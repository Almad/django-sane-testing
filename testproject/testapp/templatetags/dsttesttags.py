from django import template

register = template.Library()

class TableNode(template.Node):
    root_tmpl = u'<table>%s</table>'
    row_tmpl = u'<tr>%s</tr>'
    cell_tmpl = u'<td>%s</td>'

    def __init__(self, data):
        self.data = data

    def render(self, context):
        row_res = []
        for row in self.data:
            cell_res = []
            for cell in row:
                cell_res.append(self.cell_tmpl % cell)
            row_res.append(self.row_tmpl % u''.join(cell_res))
        return self.root_tmpl % u''.join(row_res)

@register.tag
def table(parser, token):
    args = token.contents.split()[1:]
    if len(args) < 1:
        raise template.TemplateSyntaxError("Not enough arguments for 'table'")
    return TableNode([arg.split('_') for arg in args])
