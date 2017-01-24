from django.db import models
from django.contrib.postgres.fields import IntegerRangeField, HStoreField
from people.models import Person
from polymorphic.models import PolymorphicModel


class Reference(PolymorphicModel):
    """A generic reference type which links to journal articles, books, etc."""
    title = models.CharField(max_length=200, null=True, blank=True)
    authors = models.ManyToManyField(Person, blank=True, through='Authorship')
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    doi = models.CharField(max_length=500, blank=True, null=True)

    # Ok let's try something different, things must have a bibtex entry in json
    # Can't be bothered trying to set up my own references management system, let's try just use mendeley's
    bibtex = HStoreField()

    def __str__(self):
        if self.title:
            return self.title + ' by ' + ', '.join(str(a) for a in self.authors.all())
        elif self.year:
            return ' & '.join(str(a) for a in self.authors.all()) + ', ' + str(self.year)

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


class Publisher(models.Model):
    """Journals and books have publishers"""
    name = models.CharField(max_length=500)
    city = models.CharField(max_length=200)

    def __str__(self):
        return self.name + ', ' + self.city


class Journal(models.Model):
    """Journal articles need to reference a journal"""
    name = models.CharField(max_length=400)
    abbreviation = models.CharField(max_length=300, blank=True, null=True)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name


class JournalArticle(Reference):
    """Journal articles are essentially a type of Reference model"""
    page_range = IntegerRangeField()
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE)

    # The below are all features of the particular journal issue, maybe need to get separated out?
    volume = models.PositiveIntegerField(blank=True, null=True)
    issue = models.PositiveIntegerField(blank=True, null=True)


class Book(Reference):
    """Books are essentially a type of Reference model"""
    editors = models.ManyToManyField(Person, blank=True)

    edition = models.PositiveIntegerField(blank=True, null=True)  # One to Ten, should be choices
    month = models.PositiveIntegerField(blank=True, null=True)  # Should be January - December choices
    series = models.CharField(max_length=200, blank=True, null=True)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    pages = models.PositiveIntegerField(blank=True, null=True)
    isbn = models.CharField(max_length=100, blank=True, null=True)


class BookChapter(Reference):
    """Book chapters relate to books, and are essentially a type of Reference model
    Not that happy with this as they are always going to use their parent's year but not sure what to do about it.
    Can't move year into book, journal article, etc as sometimes we have to create references without knowing what
    it is we are referencing. Not ideal. But also if the field is common to almost all models might as well have it
    in the main Reference model."""
    parent_book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapter')
    page_range = IntegerRangeField()


class WebPage(Reference):
    """WebPages are essentially a type of Reference model. Date last accessed might well be different from year,
    which should contain the year it was written in (if known)."""
    institute = models.CharField(max_length=500)
    url = models.CharField(max_length=200)
    last_accessed = models.DateTimeField()


class Thesis(Reference):
    """Theses are essentially a type of Reference model"""
    institute = models.CharField(max_length=500)
