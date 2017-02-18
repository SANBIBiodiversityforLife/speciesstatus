from django.db import models
from django.contrib.postgres.fields import IntegerRangeField, HStoreField
from people.models import Person
from polymorphic.models import PolymorphicModel


class Reference(PolymorphicModel):
    """A generic reference type which links to journal articles, books, etc."""
    title = models.CharField(max_length=500)
    authors = models.ManyToManyField(Person, blank=True, through='Authorship')
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    doi = models.CharField(max_length=500, blank=True, null=True)

    # Ok let's try something different, things must have a bibtex entry in json
    # Can't be bothered trying to set up my own references management system, let's try just use mendeley's
    bibtex = HStoreField(null=True)

    def __str__(self):
        if self.title:
            return self.title + ' by ' + ', '.join(str(a) for a in self.authors.all())
        elif self.year:
            return ' & '.join(str(a) for a in self.authors.all()) + ', ' + str(self.year)
        elif self.bibtex:
            return self.bibtex
        else:
            return "No title"

    def get_citation_for_taxon(self):
        authors = ', '.join(str(a) for a in self.authors.all())
        return authors + ', ' + str(self.year)

    def get_link(self):
        return self.get_citation_for_taxon()

    def save(self):
        super(Reference, self).save()


class Authorship(models.Model):
    person = models.ForeignKey(Person)
    reference = models.ForeignKey(Reference)
    weight = models.PositiveIntegerField(default=0)


def assign_multiple_authors(author_list, reference):
    for author in author_list:
        authorship = Authorship(reference=reference, person=author)
        authorship.save()
