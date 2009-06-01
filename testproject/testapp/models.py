from django.db import models
from django.utils.translation import ugettext_lazy as _

class ExampleModel(models.Model):
    name = models.CharField(max_length=50)

    @staticmethod
    def get_translated_string():
        return _(u"Translatable string")

    def __unicode__(self):
        return u"ExampleModel %s" % self.name