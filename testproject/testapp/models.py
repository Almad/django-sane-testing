from django.db import models

class ExampleModel(models.Model):
    name = models.CharField(max_length=50)
    
    def __unicode__(self):
        return u"ExampleModel %s" % self.name