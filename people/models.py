from django.db import models
from django.contrib.postgres.fields import IntegerRangeField


class Person(models.Model):
    first = models.CharField(max_length=200, blank=True, null=True)
    initials = models.CharField(max_length=10, blank=True, null=True)
    surname = models.CharField(max_length=200)

    lifetime = IntegerRangeField(blank=True, null=True)

    def __str__(self):
        return self.surname
