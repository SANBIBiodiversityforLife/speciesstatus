from taxa import models
from biblio import models as biblio_models
from people import models as people_models
import csv
from django.db.models import Count
import requests
import os
from django.contrib.gis.geos import Point, Polygon
import re
import datetime

def create_point_distribution(row):
    """Used by the import distribution functions"""
    if 'species' not in row or 'genus' not in row or 'long' not in row or 'lat' not in row:
        return False

    name = row['genus'].strip() + ' ' + row['species'].strip()
    if 'subspecies' in row:
        name += ' ' + row['subspecies'].strip()
    try:
        taxon = models.Taxon.objects.get(name=name)
    except models.Taxon.DoesNotExist:
        print('could not find ' + name)
        return False

    pt = models.PointDistribution(taxon=taxon, point=Point(float(row['long']), float(row['lat'])))
    optional_fields = ['precision', 'origin_code', 'qds']
    for optional_field in optional_fields:
        if optional_field in row:
            setattr(pt, optional_field, row[optional_field])

    #if 'collector' in row:
    #    pt.

    if 'year' in row and row['year'] > 0:
        month = int(float(str(row['month']).strip())) if 'month' in row else 1
        month = month if month > 0 and month < 13 else 1
        day = int(float(str(row['day']).strip())) if 'day' in row else 1
        day = day if day > 0 and day < 31 else 1
        try:
            pt.date = datetime.date(year=int(float(str(row['year']).strip())), month=month, day=day)
        except ValueError:
            import pdb; pdb.set_trace()
    pt.save()
    return pt


def create_authors(author_string):
    """
    Splits up an author string formatted as e.g. Braack, H.H., Bishop, P.J. and Knoepfer, D.
    Creates Person objects for each, and returns them in a list
    :param author_string:
    :return:
    """
    # Remove the 'and' so that we can apply a simple regex to split up the authors
    author_string = author_string.replace(' &amp; ', ', ')
    author_string = author_string.replace(' & ', ', ')
    author_string = author_string.replace(' and ', ', ')
    author_string = author_string.replace(';', ', ')
    regex = r'([A-Z][a-z]+),\s+(([A-Z]\.?)+)(,|$)'
    matches = re.findall(regex, author_string)
    people = []
    for m in matches:
        surname = m[0]
        initials = m[1]

        # Try and get all possible people in the database first
        p = people_models.Person.objects.filter(surname=surname, initials=initials).first()

        # If there's nobody there then try get same surname and no initials, it's probably the same person
        # Someone can split it out later manually if it's not
        if p is None:
            p = people_models.Person.objects.filter(surname=surname, initials__isnull=True, initials__exact='').first()
            if p is None:
                # Otherwise if we can't find anyone with the same surname make a new person
                p = people_models.Person(surname=surname, initials=initials)
            else:
                p.initials = initials
            p.save()

        people.append(p)
    return people


def fix_case(title):
    exceptions = ['a', 'an', 'the', 'is', 'of']
    word_list = re.split(' ', title)  # re.split behaves as expected
    final = [word_list[0].capitalize()]
    for word in word_list[1:]:
        final.append(word if word in exceptions else word.capitalize())
    return " ".join(final)


def get_or_create_author(surname, first=''):
    """
    Take in a surname and optional first name and try to retrieve an author from the database
    or create one if necessary
    :param surname:
    :param first:
    :return:
    """
    initials = ''
    if first != '' and first is not None:
        # If there's a dot it's definitely initials
        if '.' in first:
            initials = first.split('.')
            first = initials.pop(0).strip()
            initials = ''.join(initials)
        # If it's a very short string most probably it's a set of initials, with spaces or without
        elif len(first) < 4:
            initials = first.replace(' ', '')
            initials = list(initials)
            first = initials.pop(0).strip()
            initials = ''.join(initials)
        # If there are multiple names E.g. "Rukaya Sarah" split into first name and just store initials
        elif ' ' in first:
            initials = first.split(' ')
            first = initials.pop(0).strip()
            initials = [a[0] for a in initials]
            initials = ''.join(initials)

    # Get people with correct surname first
    p = people_models.Person.objects.filter(surname=surname).first()

    # If there's nobody there then make a new person
    if p is None:
        p = people_models.Person(surname=surname, first=first)
        p.save()
        return p

    # If there's no first name just return the surname person
    if first == '':
        return p

    # If we've got a first name then try and get the right person, or else add first name to the surname only person
    # if first != '':
    f = people_models.Person.objects.filter(surname=surname, first__iregex=r'^%s' % first).first()
    if f:
        return f
    else:
        p.first = first
        p.initials = initials
        p.save()
        return p


def create_taxon_description(authority, taxon, mendeley_session=None):
    """
    Takes in a authority string like (Barnard, 1980), splits it into year and author
    Attempts to find the author and year in mendeley and in the database, otherwise it create a new reference
    Then creates a taxonomic description for a taxon
    :param authority:
    :return:
    """

    # Splits up an authority string formatted in the standard way e.g. (Barnard, 1937) into year and author
    bracketed = '(' in authority
    authority = re.sub('[()]', '', authority)
    # Split into year + authors
    matches = re.findall(r'\d{4}', authority)
    if matches and len(matches) == 1:
        year = matches[0]
        authors = re.sub(',?\s*\d{4},?', '', authority).strip()
    else:
        print('no year found or many years found') # Someone is going to have to fix this
        year = 0
        authors = authority
    cits = []

    if mendeley_session:
        # Try and find citation
        try:
            rs = mendeley_session.catalog.advanced_search(author=authors, min_year=year, max_year=year, view='bib')

            # Kind of embarrassing but i can't work out how to get len(rs.iter())
            for r in rs.iter():
                cits.append(r)
        except:
            import pdb;
            pdb.set_trace()

    # If we get only one result then hurrah we can use it to populate our references table
    if len(cits) == 1:
        cit = cits[0]

        # Get the authors from the mendeley result
        author_list = []
        for a in cit.authors:
            author = get_or_create_author(surname=a.last_name, first=a.first_name)
            author_list.append(author)

        # Get any reference which looks good in the db
        reference = biblio_models.Reference.objects.filter(authors__in=author_list, year=cit.year,
                                                           title__iexact=cit.title).annotate(num_tags=Count('authors')) \
            .filter(num_tags=len(author_list))

        # Hmm maybe we can just assume if title and year are the same it's all good? Let's try...
        reference = biblio_models.Reference.objects.filter(year=cit.year, title__iexact=cit.title)

        # If we couldn't find a reference we need to make one
        if len(reference) < 1:
            reference = biblio_models.Reference(year=cit.year, title=cit.title)
            reference.save()
            biblio_models.assign_multiple_authors(author_list=author_list, reference=reference)

            #if cit.type == 'journal':
            #    biblio_models.Journal.objects.get_or_create(name=cit.source)
        else:
            reference = reference[0]
    # If we didn't get 1 mendeley result we need to add what reference info we can to the db
    else:
        # Insert or create authors
        author_list = []
        for surname in authors.split('&'):
            author = get_or_create_author(surname=surname)
            author_list.append(author)

        # Get citation reference, use whatever we can find in db
        print('getting citation reference from db...')
        reference = []
        try:
            reference = biblio_models.Reference.objects.filter(authors__in=author_list, year=year) \
                .annotate(num_tags=Count('authors')).filter(num_tags=len(author_list))
        except:
            import pdb; pdb.set_trace()

        # If we couldn't find a reference we need to make one
        if len(reference) < 1:
            reference = biblio_models.Reference(year=year)
            reference.save()
            biblio_models.assign_multiple_authors(author_list=author_list, reference=reference)
        elif len(reference) == 0:
            return
        else:
            reference = reference[0]

    # Make the description
    description, created = models.Description.objects.get_or_create(reference=reference,
                                                                    taxon=taxon,
                                                                    weight=int(bracketed))
    return description, created

