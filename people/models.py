from django.db import models
from django.contrib.postgres.fields import IntegerRangeField, ArrayField
from django.utils.text import slugify


class Person(models.Model):
    first = models.CharField(max_length=300, blank=True, null=True)
    initials = models.CharField(max_length=15, blank=True, null=True)
    surname = models.CharField(max_length=300)
    slug = models.SlugField(max_length=500)

    lifetime = IntegerRangeField(blank=True, null=True)
    email = ArrayField(
        models.CharField(max_length=200), null=True, blank=True
    )

    def __str__(self):
        returned_name = self.surname
        if self.initials:
            returned_name = self.initials + ' ' + returned_name
        if self.first:
            returned_name = self.first + ' ' + returned_name

        return returned_name

    # Overrides the default save so that we can get a nice URL
    def save(self, *args, **kwargs):
        if not self.pk:
            self.slug = slugify(str(self))

        super(Person, self).save(*args, **kwargs)