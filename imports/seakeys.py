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
from imports import views as imports_views


def import_helper(item, rank_name, parent):
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
        imports_views.create_taxon_description(authority, taxon)
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
                        parent = import_helper(item=item, rank_name=rank_name, parent=parent)
                        break

            # Finally the species can get added, provided of course that it is a species
            if rank != 'Genus' and rank != 'Family':
                parent = import_helper(item=worms_taxon, rank_name='Species', parent=parent)

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