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
<<<<<<< HEAD
from imports import sis_import, spstatus_import, sarca_sabca, sabca
=======
from imports import sis_import, spstatus_import
from imports import seakeys as seakeys_import
>>>>>>> 220ceaf7cd403315ebd1c9c60914c7be29e7d073
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
<<<<<<< HEAD
    authority = authority.split(',')
    year = authority[-1].strip()
    year = re.sub('[^0-9]', '', year)
    authors = authority[0]
=======
    # Split into year + authors
    matches = re.findall(r'\d{4}', authority)
    if matches and len(matches) == 1:
        year = matches[0]
        authors = re.sub(',?\s*\d{4},?', '', authority).strip()
    else:
        print('no year found or many years found') # Someone is going to have to fix this
        year = 0
        authors = authority
>>>>>>> 220ceaf7cd403315ebd1c9c60914c7be29e7d073
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


def sis(request):
    sis_import.import_sis()

def sarca(request):
    sarca_sabca.import_sql()

def sabca_r(request):
    sabca.import_sabca_sql()

<<<<<<< HEAD
def spstatus(request):
    spstatus_import.import_spstatus()
=======
def seakeys(request):
    seakeys_import.import_seakeys()


def insert_bird_distrib_data(request):
    pwd = os.path.abspath(os.path.dirname(__file__))
    dir = os.path.join(pwd, '..', 'data-sources', 'bird_redlist_distribs')

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


def download_missing_images(request):
    # Could also try
    # gbif
    # http://api.gbif.org/v1/species?name=Acanthocercus%20atricollis
    # http://api.gbif.org/v1/species/5225997/media
    # bold
    # http://www.boldsystems.org/index.php/API_Tax/TaxonSearch?taxName=Diplura
    # http://www.boldsystems.org/index.php/API_Tax/TaxonData?taxId=88899&dataTypes=images
    # arkive
    # https://www.arkive.org/api/docs?ReturnUrl=%2fapi%2fdocs%2fembed%2fgenerate
    # inaturalist
    # https://www.inaturalist.org/pages/api+reference#get-observations

    eol_search_sp_url = 'http://eol.org/api/search/1.0.json?q={0}&page=1&exact=true&filter_by_taxon_concept_id=&filter_by_hierarchy_entry_id=&filter_by_string=&cache_ttl='
    eol_img_url = 'http://eol.org/api/pages/1.0.json?batch=false&id={0}&images_per_page=1&images_page=1&videos_per_page=0&videos_page=0&sounds_per_page'

    species_rank = models.Rank.objects.get(name='Species')
    subspecies_rank = models.Rank.objects.get(name='Subspecies')
    taxa =  models.Taxon.objects.filter(rank__in=[species_rank, subspecies_rank]).order_by('name').values_list('name', flat=True)

    for taxon in taxa:
        file_name = taxon.replace(' ', '_') + '.jpg'
        if not os.path.exists(os.path.join(settings.BASE_DIR, 'website', 'static', 'sp_img', file_name)):
            eol_sp_search = requests.get(eol_search_sp_url.format(taxon.replace(' ', '+')))
            results = eol_sp_search.json()['results']
            if len(results) == 0:
                print('No sp found ' + taxon)
                continue
            id = results[0]['id']
            eol_img_search = requests.get(eol_img_url.format(id))
            imgs = eol_img_search.json()['dataObjects']
            found = False
            for img in imgs:
                if img['dataType'] == 'http://purl.org/dc/dcmitype/StillImage':
                    if 'license' in img and 'mimeType' in img and 'eolMediaURL' in img:
                        print('FOUND ' + taxon)
                        found = True
            if not found:
                print('NOT FOUND ' + taxon)
                # print(imgs)


def load_dragonfly_distribs(request):
    # Load all other things as well
    # spstatus_import.import_spstatus()
    # sis_import.import_sis()

    dir = 'C:\\Users\\JohaadienR\\Documents\\Projects\\python-sites\\species\\data-sources\\dragonflies_distrib\\'
    df = pd.read_csv(dir + 'simple.csv')
    for index, row in df.iterrows():
        row = {k.lower(): v for k, v in row.items() if pd.notnull(v)}
        if 'species' not in row or 'genus' not in row or 'decimal_longitude' not in row or 'decimal_latitude' not in row:
            continue
        try:
            taxon = models.Taxon.objects.get(name=row['genus'].strip() + ' ' + row['species'].strip())
        except:
            print('could not find ' + row['genus'].strip() + ' ' + row['species'].strip())
            continue

        print('found ' + row['genus'].strip() + ' ' + row['species'].strip())
        pt = models.PointDistribution.objects.create(taxon=taxon, point=Point(float(row['decimal_longitude']), float(row['decimal_latitude'])))


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
        print(taxon.name.lower())
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
        except (KeyError, IndexError, UnicodeDecodeError):
            import pdb; pdb.set_trace()
        # common_name.save()

    #r = requests.get('http://api.gbif.org/v1/species?' + )
    #r.json()

>>>>>>> 220ceaf7cd403315ebd1c9c60914c7be29e7d073
