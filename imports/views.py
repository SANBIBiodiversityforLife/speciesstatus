from django.shortcuts import render
from taxa import models
from biblio import models as biblio_models
from people import models as people_models
from redlist import models as redlist_models
import csv
from suds.client import Client
import requests
from mendeley import Mendeley
import re
from django.db.models import Count
from django.http import HttpResponse
import pandas as pd
from psycopg2.extras import NumericRange
from imports import sis_import, spstatus_import, sarca_sabca, sabca
from imports import sis_import, spstatus_import
from imports import seakeys as seakeys_import
import pdb
import re
import requests
import json
import os
import urllib.request
from django.conf import settings
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.geos import GEOSGeometry
import re
import datetime

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


def import_phylums(request):
    sis_import.import_phylums()


# SIS: Amphibian, Mammals, Dragonflies, Reptiles, Freshwater Fish
def sis(request):
    sis_import.import_sis()


# Butterflies
def sarca(request):
    sarca_sabca.import_sql()


# Reptiles - going to move to SIS though
def sabca_r(request):
    sabca.import_sabca_sql()


# Legacy data - we're not importing this
def spstatus(request):
    spstatus_import.import_spstatus()


# Linefish
def seakeys(request):
    seakeys_import.import_seakeys()


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


# Note: Birds are run from the other django app
def bird_distribs(request):
    pwd = os.path.abspath(os.path.dirname(__file__))
    dir = os.path.join(pwd, '..', 'data-sources', 'bird_distribs')

    bird_parent_node = models.Taxon.objects.get(name='Aves')
    species_rank = models.Rank.objects.get(name='Species')
    subspecies_rank = models.Rank.objects.get(name='Subspecies')
    birds = bird_parent_node.get_descendants().filter(rank__in=[species_rank, subspecies_rank])
    for bird in birds:
        bird_file = os.path.join(dir, bird.name.replace(' ', '_') + '.json')
        if not os.path.exists(bird_file):
            continue

        with open(bird_file) as data_file:
            distributions = json.load(data_file)

            for distribution in distributions['features']:
                polygon_points = []
                for ring in distribution['geometry']['rings'][0]:
                    polygon_points.append((ring[0], ring[1]))
                polygon_tuple = tuple(polygon_points)
                polygon = Polygon(polygon_tuple, srid=4326)
                distrib = models.GeneralDistribution(taxon=bird, distribution_polygon=polygon)
                distrib.save()


def convert_all_criteria_strings(request):
    needs_fixing = redlist_models.Assessment.objects.filter(redlist_criteria__contains='|')

    for assessment in needs_fixing:
        try:
            assessment.redlist_criteria = convert_criteria_string(assessment.redlist_criteria)
        except IndexError:
            import pdb; pdb.set_trace()
        assessment.save()


def convert_criteria_string(string):
    # Construct a load of nested dictionaries with all of the individual components
    cons = {}
    for item in string.split('|'):
        # B
        letter = item[0].upper()
        if letter not in cons:
            cons[letter] = {}

        # B1, sometimes you just have D with no number
        if len(item) > 1:
            number = item[1]
            if number not in cons[letter]:
                cons[letter][number] = {}

            # B1a or B1b_iii, sometimes you just have D1 with no letter
            if len(item) > 2:
                small_letter = item[2].lower()
                if small_letter not in cons[letter][number]:
                    cons[letter][number][small_letter] = []

                if '_' in item:
                    roman_numerals = item.split('_')[1]
                    if roman_numerals not in cons[letter][number][small_letter]:
                        cons[letter][number][small_letter].append(roman_numerals)

    # Following is not used, just an example of what we're constructing
    # output_example = {'A': {'2': {'a': [], 'b': []}}, 'B': {'1': {'a': [], 'b': ['i', 'ii', 'iii']}}}

    # Join those dictionaries together, we also need to do some sorting once they are lists
    letter_strings = []
    for letter, number_dict in cons.items():
        number_strings = []

        for number, small_letter_dict in number_dict.items():
            small_letter_strings = []

            for small_letter, roman_numerals_list in small_letter_dict.items():
                small_letter_string = small_letter
                if roman_numerals_list:
                    small_letter_string += '(' + ','.join(roman_numerals_list) + ')'
                small_letter_strings.append(small_letter_string)

            # small_letter_string now looks like this: 'ab(i,ii,iii)'
            number_strings.append(number + ''.join(sorted(small_letter_strings)))

        # number_strings now looks like this ['2ab(i,ii,iii)', '1a']
        letter_strings.append(letter + '+'.join(sorted(number_strings)))

    # letter_strings now looks like this ['A2ab(i,ii,iii)', 'C1a']

    return '; '.join(sorted(letter_strings))


def reptile_distribs(request):
    pwd = os.path.abspath(os.path.dirname(__file__))
    dir = os.path.join(pwd, '..', 'data-sources', 'reptile_distribs')
    df = pd.read_csv(os.path.join(dir, 'simple.csv'), encoding='latin-1')
    mapping = {'decimalLat': 'lat',
               'decimalLon': 'long',
               'institution_code': 'Institutio',
               'year_colle': 'year',
               'month_coll': 'month',
               'day_collec': 'day'}
    for index, row in df.iterrows():
        row = {k.lower(): v for k, v in row.items() if pd.notnull(v)}
        for key in mapping:
            if key in row:
                row[mapping[key]] = row[key]
                del row[key]
        pt = create_point_distribution(row)


def dragonfly_distribs(request):
    pwd = os.path.abspath(os.path.dirname(__file__))
    dir = os.path.join(pwd, '..', 'data-sources', 'dragonfly_distribs')
    df = pd.read_csv(os.path.join(dir, 'simple.csv'))
    mapping = {'decimal_latitude': 'lat',
               'decimal_longitude': 'long',
               'institution_code': 'origin_code',
               'coordinate_uncertainty_in_meters': 'precision',
               'year_collected': 'year',
               'month_collected': 'month',
               'day_collected': 'day'}
    for index, row in df.iterrows():
        row = {k.lower(): v for k, v in row.items() if pd.notnull(v)}
        for key in mapping:
            if key in row:
                row[mapping[key]] = row[key]
                del row[key]
        pt = create_point_distribution(row)


def mammal_distribs(request):
    pwd = os.path.abspath(os.path.dirname(__file__))
    dir = os.path.join(pwd, '..', 'data-sources', 'mammal_distribs')
    mapping = {'decimallatitude': 'lat',
               'decimallongitude': 'long',
               'institutioncode': 'origin_code',
               'coordinateuncertaintyinmeters': 'precision',
               'specificepithet': 'species'}
    for file in os.listdir(dir):
        df = pd.read_excel(os.path.join(dir, file))
        for index, row in df.iterrows():
            row = {k.lower(): v for k, v in row.items() if pd.notnull(v)}
            for key in mapping:
                if key in row:
                    row[mapping[key]] = row[key]
                    del row[key]
            pt = create_point_distribution(row)
            if pt:
                import pdb; pdb.set_trace()


# Run after all of the imports have gone through
def populate_higher_level_common_names(request):
    ranks = models.Rank.objects.filter(name__in=['Genus', 'Family', 'Order', 'Phylum', 'Class'])
    taxa = models.Taxon.objects.filter(rank__in=ranks, common_names__isnull=True)
    english = models.Language.objects.get(name='English')

    # Manually found some nodes common names
    pwd = os.path.abspath(os.path.dirname(__file__))
    common_names = {}
    with open(os.path.join(pwd, '..', 'data-sources', 'common_names.csv')) as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            common_names[row[0]] = row[1]

    for taxon in taxa:
        taxon_name = taxon.name.lower()

        # Try and get it in my list first
        if taxon_name in common_names:
            common_name = models.CommonName.objects.get_or_create(name=common_names[taxon_name], taxon=taxon, language=english)
            continue

        # Otherwise search GBIF
        r = requests.get('http://api.gbif.org/v1/species/search?q=' + taxon.name.lower() + '&rank=' + str(taxon.rank))
        gbif = r.json()
        print('-----')
        try:
            print(taxon.name.lower())
        except:
            print('could not print')
        #import pdb; pdb.set_trace()
        try:
            for result in gbif['results']:
                if 'vernacularNames' in result and len(result['vernacularNames']) > 0:
                    for vn in result['vernacularNames']:
                        if vn['language'].lower() == '' or vn['language'].lower() == 'english':
                            common_name_text = vn['vernacularName'] # Reasonable to assume english?
                            common_name = models.CommonName.objects.get_or_create(name=common_name_text, taxon=taxon, language=english)
                            print('GBIF ' + taxon.name.lower() + ' : ' + common_name_text)
                            break
        except (KeyError, IndexError, UnicodeDecodeError, UnicodeEncodeError):
            import pdb; pdb.set_trace()
        # common_name.save()

    #r = requests.get('http://api.gbif.org/v1/species?' + )
    #r.json()

