from django.db import models
from django.contrib.postgres.fields import IntegerRangeField, ArrayField


class Person(models.Model):
    first = models.CharField(max_length=200, blank=True, null=True)
    initials = models.CharField(max_length=10, blank=True, null=True)
    surname = models.CharField(max_length=200)

    lifetime = IntegerRangeField(blank=True, null=True)
    email = ArrayField(
        models.CharField(max_length=200), null=True, blank=True
    )

    def __str__(self):
        if self.first:
            return self.first + ' ' + self.surname
        else:
            return self.surname
