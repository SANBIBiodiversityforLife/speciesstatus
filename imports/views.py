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


def get_or_create_author(surname, first=''):
    initials = ''
    if first != '':
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


def create_taxon_description(authority, taxon):
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
    authority = authority.split(',')
    year = authority[-1].strip()
    authors = authority[0]

    # Sanity check, authority should have been split up into year and author list of length 2
    if len(authority) < 2:  # Someone is going to have to fix this...
        year = '0'

    # Try and find citation
    try:
        rs = mendeley_session.catalog.advanced_search(author=authors, min_year=year, max_year=year, view='bib')

        # Kind of embarrassing but i can't work out how to get len(rs.iter())
        cits = []
        for r in rs.iter():
            cits.append(r)
    except:
        import pdb;
        pdb.set_trace()

    # If we get only one result then hurrah we can use it to populate our references table
    if len(cits) == 1:
        cit = cits[0]

        # Get the authors
        author_list = []
        for a in cit.authors:
            author = get_or_create_author(surname=a.last_name, first=a.first_name)
            author_list.append(author)

        # Get any reference which looks good in the db
        reference = biblio_models.Reference.objects.filter(authors__in=author_list, year=cit.year,
                                                           title__iexact=cit.title).annotate(num_tags=Count('authors')) \
            .filter(num_tags=len(author_list))

        # Hmm maybe we can just assume title and year? Let's try...
        reference = biblio_models.Reference.objects.filter(year=cit.year, title__iexact=cit.title)

        # If we couldn't find a reference we need to make one
        if len(reference) < 1:
            reference = biblio_models.Reference(year=cit.year, title=cit.title)
            reference.save()
            biblio_models.assign_multiple_authors(author_list=author_list, reference=reference)

            if cit.type == 'journal':
                biblio_models.Journal.objects.get_or_create(name=cit.source)
        else:
            reference = reference[0]
    else:
        # Insert or create authors
        author_list = []
        for surname in authors.split('&'):
            author = get_or_create_author(surname=surname)
            author_list.append(author)

        # Get citation reference, use whatever we can find in db
        print('getting citation reference from db...')
        try:
            reference = biblio_models.Reference.objects.filter(authors__in=author_list, year=year) \
                .annotate(num_tags=Count('authors')).filter(num_tags=len(author_list))
        except:
            import pdb;
            pdb.set_trace()

        # If we couldn't find a reference we need to make one
        if len(reference) < 1:
            reference = biblio_models.Reference(year=year)
            reference.save()
            biblio_models.assign_multiple_authors(author_list=author_list, reference=reference)

        else:
            reference = reference[0]

    # Make the description
    description, created = models.Description.objects.get_or_create(reference=reference,
                                                                    taxon=taxon,
                                                                    weight=int(bracketed))


def import_helper(item, mendeley_session, rank_name, parent):
    name = item['valid_name']
    if 'valid_authority' in item:
        authority = item['valid_authority']
    else:
        authority = item['authority']

    # Create new taxon
    rank = models.Rank.objects.get(name=rank_name)
    taxon, created = models.Taxon.objects.get_or_create(parent=parent, name=name, rank=rank)

    if authority is None:
        print('Authority is none\n')
        print(item)
        print('\n\n')

    if created and authority is not None:
        create_taxon_description(authority, taxon)
    return taxon


def import_seakeys(request):
    # Load the images csv into a dict for reference later
    file_loc = 'C:\\Users\\JohaadienR\\Documents\\Projects\\python-sites\\species\\images.csv'
    reader = csv.DictReader(open(file_loc))
    images = {}
    for row in reader:
        images[row['Nid'].strip()] = row['Image'].strip()

    # Start the WOrms name query SOAP client
    url = 'http://www.marinespecies.org/aphia.php?p=soap&wsdl=1'
    client = Client(url)

    # Start the REST client for mendeley to try and automatically find publications
    mendeley_id = '3513'
    mendeley_secret = 'gOVvM5RmKseDgcmH'
    mendeley_redirect = 'http://species.sanbi.org'
    mendeley = Mendeley(mendeley_id, client_secret=mendeley_secret, redirect_uri=mendeley_redirect)
    mendeley_session = mendeley.start_client_credentials_flow().authenticate()

    # Iterate through the csv
    file_loc = 'C:\\Users\\JohaadienR\\Documents\\Projects\\python-sites\\species\\seakeys.csv'
    reader = csv.DictReader(open(file_loc, encoding='ISO-8859-1'))
    for row in reader:
        # Start at the bottom, find the species and grab higher taxa from WoRMS
        species_name = row['Genus'] + ' ' + row['Species']
        rank = 'Species'

        # In one or two cases we add genuses not species
        if row['Species'].strip() == '':
            species_name = row['Genus']
            rank = 'Genus'

            if row['Genus'] == '':
                species_name = row['Family']
                rank = 'Family'

        search_results = client.service.getAphiaRecords(species_name, like='false', marine_only='true')
        try:
            worms_taxon = search_results[0]
        except:
            import pdb; pdb.set_trace()

        # Sanity check
        try:
            if worms_taxon['rank'].lower() != rank.lower():
                print(rank.lower() + ' != ' + worms_taxon['rank'].lower())
                import pdb
                pdb.set_trace()

            # Get the higher taxa
            worms_taxa = [('Phylum', worms_taxon['phylum']),
                          ('Class', worms_taxon['cls']),
                          ('Order', worms_taxon['order']),
                          ('Family', worms_taxon['family']),
                          ('Genus', worms_taxon['genus'])]

            # Preset the Kingdom as parent ready for the for loop below
            kingdom_rank = models.Rank.objects.get(name='Kingdom')
            parent = models.Taxon.objects.get(name=row['Kingdom'], rank=kingdom_rank)

            # Run through all of the worms_taxa and create a new object in the tree for them
            for taxa in worms_taxa:
                rank_name = taxa[0]
                name = taxa[1]
                search_results = client.service.getAphiaRecords(name, like='false', marine_only='true')
                for item in search_results:
                    if item['rank'].lower() == rank_name.lower():
                        parent = import_helper(item=item, mendeley_session=mendeley_session, rank_name=rank_name, parent=parent)
                        break

            # Finally the species can get added, provided of course that it is a species
            if rank != 'Genus' and rank != 'Family':
                parent = import_helper(item=worms_taxon, mendeley_session=mendeley_session, rank_name='Species', parent=parent)

            # Now we can add our taxa info to it!
            try:
                description = models.Info.objects.get(taxon=parent)
            except models.Info.DoesNotExist:
                description = models.Info(taxon=parent,
                                          morphology=row['Description'],
                                          movement=row['Ecology - movement'],
                                          reproduction=row['Ecology - reproduction'],
                                          trophic=row['Ecology - trophic strategy'],
                                          uses=row['Uses and exploitation'],
                                          distribution=row['Southern Africa distribution'],
                                          habitat=row['Habitat - other'])
                description.save()

                if row['Images'].strip():
                    for img in row['Images'].split(','):
                        img_nid = img.strip()

                        if img_nid:
                            # Lookup nid in dictionary loaded earlier
                            file_name = images[img_nid]
                            path = 'http://seakeys.sanbi.org/sites/default/files/seakey-images/'
                            url = path + file_name
                            new_image = models.Image(taxon=parent, url=url)
                            new_image.save()

                if row['Common names'].strip():
                    for name in row['Common names'].split(','):
                        name = name.strip()
                        if name:
                            english, created = models.Language.objects.get_or_create(name='English')

                            # Use get or create so we don't add same common name twice
                            models.CommonName.objects.get_or_create(language=english, taxon=parent, name=name)
        except:
            continue


def import_sis(request):
    dir = 'C:\\Users\\JohaadienR\\Documents\\Projects\\python-sites\\species\\data-sources\\'
    af = pd.read_csv(dir + 'Amphibians_SIS\Amphibians\\allfields.csv', encoding='iso-8859-1')
    t = pd.read_csv(dir + 'Amphibians_SIS\Amphibians\\taxonomy.csv')
    cn = pd.read_csv(dir + 'Amphibians_SIS\Amphibians\\commonnames.csv')

    # Any duplicates?
    if len(t.loc[t.duplicated('Redlist_id'), :]) != 0 or len(af.loc[af.duplicated('internal_taxon_id'), :]) != 0:
        print('Error, duplicates')
        import pdb; pdb.set_trace()

    # Merged
    df = pd.merge(af, t, left_on='internal_taxon_id', right_on='internal_taxon_id', how='left')

    # Create all taxon objects
    # df.apply(create_taxon_from_sis, axis=1)
    for index, row in df.iterrows():
        species = create_taxon_from_sis(row)

        # Bit inelegant, what I am doing down here is creating an info model only if/with relevant info to go in it
        if row['AvgAnnualFecundity.fecundity'] or \
                row['BirthSize.size'] or \
                row['Congregatory.value'] or \
                row['EggLaying.layEggs'] or \
                row['ElevationLower.limit']:
            info = models.Info(taxon=species)
            if row['AvgAnnualFecundity.fecundity']:
                info.average_fecundity = row['AvgAnnualFecundity.fecundity']
            if row['BirthSize.size']:
                info.birth_size = row['BirthSize.size']
                info.size_units = models.Info.CM
            if row['Congregatory.value']:
                info.congregatory = [models.Info.CONGREGATORY, models.Info.DISPERSIVE] # These all seem to be the same
            if row['EggLaying.layEggs'] == 'Yes':
                info.reproductive_type = [models.Info.EGG_LAYING]
            elif row['EggLaying.layEggs'] == 'No':
                info.reproductive_type = [models.Info.LIVE_BIRTH]
            if row['FreeLivingLarvae.hasStage'] == 'Yes':
                info.reproductive_type = [models.Info.FREE_LIVING_LARVAE]
            if row['MaxSize.size']:
                info.max_size = row['MaxSize.size']
                info.size_units = models.Info.CM
            if row['ElevationLower.limit'] and	row['ElevationUpper.limit']:
                info.altitude_or_depth_range = (int(row['ElevationLower.limit']), int(row['ElevationUpper.limit']))
            info.save()

        columns_to_exclude = [
            'AvgAnnualFecundity.fecundity',
            'BirthSize.size',
            'MaxSize.size',
            'Congregatory.value',
            'EggLaying.layEggs',
            'FreeLivingLarvae.hasStage',
            'AOO.range',
            'EOO.range',
            'ElevationLower.limit',
            'ElevationUpper.limit',
        ]

        misc = {
        }

        a = redlist_models.Assessment(
            taxon=species,
            area_occupancy=NumericRange(row['AOO.range'], row['AOO.range']),
            extent_occurrence=NumericRange(row['EOO.range'], row['EOO.range']),
        )
        a.save()


	
    import pdb; pdb.set_trace()
    print('done')
    return HttpResponse('<html><body><p>Done</p></body></html>')


def create_taxon_from_sis(row):
    """
    Adds to the taxa hierarchy from SIS
    :param row:
    :return:
    """
    # Preset the Animalia Kingdom as parent ready for the for loop below
    kingdom_rank = models.Rank.objects.get(name='Kingdom')
    parent = models.Taxon.objects.get(name='Animalia', rank=kingdom_rank)

    # Make a list of the taxa hierarchy from the SIS row in the csv to iterate over
    taxa_hierarchy = [
        ['phylum', row['phylum']],
        ['class', row['classname']],
        ['order', row['ordername']],
        ['family', row['family']],
        ['genus', row['genus']],
    ]
    for t in taxa_hierarchy:
        rank = models.Rank.objects.get(name=t[0])
        taxon_name = t[1].strip().capitalize()
        parent, created = models.Taxon.objects.get_or_create(parent=parent, name=taxon_name, rank=rank)

    # Finally add the species to the taxa hierarchy
    rank = models.Rank.objects.get(name='species')
    species_name = parent.name + ' ' + row['species'].strip()
    species, created = models.Taxon.objects.get_or_create(parent=parent, name=species_name, rank=rank)

    # Add taxon notes if there are any
    taxon_notes = row['TaxonomicNotes.value']
    if taxon_notes is not None and taxon_notes != '':
        species.notes = taxon_notes
        species.save()

    # Create a description and set of references
    create_taxon_description(row['taxonomicAuthority'], species)

    return species


