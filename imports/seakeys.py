from taxa import models
from biblio import models as biblio_models
from people import models as people_models
from redlist import models as redlist_models
import csv
from suds.client import Client
from mendeley import Mendeley
import re
from imports import views as imports_views
import os
import shutil
from django.conf import settings
import subprocess
import datetime


def import_helper(item, rank_name, parent, mendeley_session):
    name = item['valid_name']
    if 'valid_authority' in item:
        authority = item['valid_authority']
    else:
        authority = item['authority']

    # Create new taxon
    rank = models.Rank.objects.get(name=rank_name)
    taxon, created = models.Taxon.objects.get_or_create(parent=parent, name=name, rank=rank)

    #if authority is None:
    #    print('Authority is none\n')
    #    print(item)
    #    print('\n\n')

    if created and authority is not None:
        imports_views.create_taxon_description(authority, taxon, mendeley_session)
    return taxon


def import_seakeys():
    # Start the REST client for mendeley, best to maintain the session throughout the data import
    # Mendeley API doesn't like us instantiating many sessions
    mendeley_id = '3513'
    mendeley_secret = 'gOVvM5RmKseDgcmH'
    mendeley_redirect = 'http://species.sanbi.org'
    mendeley = Mendeley(mendeley_id, client_secret=mendeley_secret, redirect_uri=mendeley_redirect)
    mendeley_session = mendeley.start_client_credentials_flow().authenticate()

    # Load the images csv into a dict for reference later
    pwd = os.path.abspath(os.path.dirname(__file__))
    pwd = os.path.join(pwd, '..', 'data-sources', 'seakeys')
    images = {}
    with open(os.path.join(pwd, 'images.csv'), encoding="utf8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            images[row['Nid'].strip()] = row

    # Load the references csv into a dict for reference later
    references = {}
    with open(os.path.join(pwd, 'refs.csv'), encoding="utf8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            references[row['Nid'].strip()] = row
    ref_mapper = {
        'Thesis': 'phdthesis',
        'Journal Article': 'article',
        'Conference Paper': 'inproceedings',
        'Miscellaneous': 'misc',
        'Report': 'techreport',
        'Book': 'book',
        'Newspaper Article': 'article',
        'Book Chapter': 'inbook',
        'Government Report': 'techreport',
        'Website': 'electronic',
        'Unpublished': 'unpublished',
        'Web Article': 'electronic',
        'Journal': 'article',
        'Web service': 'electronic',
        'Database': 'electronic',
        'Web project page': 'electronic',
        'Conference Proceedings': 'proceedings'
    }
    ref_field_mapper = {'DOI': 'doi',
                        'Issue': 'edition',
                        'Place Published': 'address',
                        'Publisher': 'publisher',
                        'Volume': 'volume',
                        'Year of Publication': 'year'}

    # Start the WOrms name query SOAP client
    url = 'http://www.marinespecies.org/aphia.php?p=soap&wsdl=1'
    client = Client(url)

    # Iterate through the csv
    csv_file = os.path.join(pwd, 'seakeys.csv')
    reader = csv.DictReader(open(csv_file, encoding='ISO-8859-1'))
    for row in reader:
        #if reader.line_num < 114:
        #    continue
        print(row['Genus'] + ' ' + row['Species'])
        # Skip all of the species with no assessments
        if row['Regional status 2015'].strip() == '':
            continue

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

        if species_name == 'Maculabatis gerrardi':
            search_results = client.service.getAphiaRecords('Himantura alcockii', like='false', marine_only='true')
        else:
            search_results = client.service.getAphiaRecords(species_name, like='false', marine_only='true')
        try:
            worms_taxon = search_results[0]
        except:
            import pdb; pdb.set_trace()

        # Sanity check
        if worms_taxon['rank'].lower() != rank.lower():
            print(rank.lower() + ' != ' + worms_taxon['rank'].lower())
            import pdb; pdb.set_trace()

        # Get the higher taxa
        worms_taxa = [('Phylum', worms_taxon['phylum']),
                      ('Class', worms_taxon['cls']),
                      ('Order', worms_taxon['order']),
                      ('Family', worms_taxon['family']),
                      ('Genus', worms_taxon['genus'])]

        # Preset the Kingdom as parent ready for the for loop below
        parent = models.Taxon.objects.get(name='Animalia')

        # Run through all of the worms_taxa and create a new object in the tree for them
        for taxa in worms_taxa:
            rank_name = taxa[0]
            name = taxa[1]
            search_results = client.service.getAphiaRecords(name, like='false', marine_only='true')
            for item in search_results:
                if item['rank'].lower() == rank_name.lower():
                    parent = import_helper(item=item, rank_name=rank_name, parent=parent, mendeley_session=mendeley_session)
                    break

        # Finally the species can get added, provided of course that it is a species
        if rank != 'Genus' and rank != 'Family':
            parent = import_helper(item=worms_taxon, rank_name='Species', parent=parent, mendeley_session=mendeley_session)

        # Now we can add our taxa info to it!
        # description = models.Info.objects.get_or_create(taxon=parent)
        description = models.Info(taxon=parent,
                                  morphology=row['Description'],
                                  movement=row['Ecology - movement'],
                                  reproduction=row['Ecology - reproduction'],
                                  trophic=row['Ecology - trophic strategy'],
                                  habitat_narrative=row['Habitat - other'])
        # Ecology - other
        # Habitat
        # Legislation
        # Other
        # Residency status
        description.save()

        assessment = redlist_models.Assessment(taxon=parent,
                                               population_trend_narrative=row['Population description'],
                                               temp_field={'Trend': row['Population trend']},
                                               redlist_criteria=row['Redlist criteria'],
                                               rationale=row['Redlist rationale'],
                                               scope=redlist_models.Assessment.REGIONAL,
                                               date=datetime.date(2015, 1, 1),
                                               redlist_category=row['Regional status 2015'].strip(),
                                               threats_narrative=row['Threats'],
                                               distribution_narrative=row['Southern Africa distribution'],
                                               use_trade_narrative=row['Uses and exploitation'])
        assessment.save()

        # Add the contributors, they come in this format: Rose Thornycroft, Rukaya Johaadien
        for i, contributor in enumerate(row['Redlist assessor'].split(',')):
            contributor = contributor.strip()
            names = contributor.split(' ')
            try:
                if len(names) == 2:
                    person, created = people_models.Person.objects.get_or_create(first=names[0], surname=names[1])
                else:
                    person, created = people_models.Person.objects.get_or_create(surname=names[0])
            except:
                import pdb; pdb.set_trace()
            c = redlist_models.Contribution(person=person, assessment=assessment, weight=i,
                                            type=redlist_models.Contribution.ASSESSOR)
            c.save()
        for i, contributor in enumerate(row['Redlist reviewer'].split(',')):
            contributor = contributor.strip()
            names = contributor.split(' ')
            try:
                if len(names) == 2:
                    person, created = people_models.Person.objects.get_or_create(first=names[0], surname=names[1])
                else:
                    person, created = people_models.Person.objects.get_or_create(surname=names[0])
            except:
                import pdb; pdb.set_trace()
            c = redlist_models.Contribution(person=person, assessment=assessment, weight=i,
                                            type=redlist_models.Contribution.REVIEWER)
            c.save()

        if row['References'].strip():
            for ref_nid in row['References'].split(','):
                ref_nid = ref_nid.strip()
                reference = references[ref_nid]
                type = ref_mapper[reference['Type of Publication']]

                if 'phd' in reference['Type of Work']:
                    type = 'phdthesis'

                # Format: M.J. Smale; A.J.J. Goosen
                if reference['Authors'] == 'N.E.P.T.A.L.Í. Morales-Serna; S. Gomez; G.E.R.A.R.D.O.P.É.R.E.Z.P.O.N. De Leon':
                    reference['Authors'] = 'N. Morales-Serna; S. Gomez; G.P. De Leon'
                if reference['Authors'] == 'M.A.L.C.O.L.M.P. Francis':
                    reference['Authors'] = 'M.P. Francis'
                if reference['Authors'] == 'S.T.U.A.R.T.W.I.L.L.I.A.M. Dunlop':
                    reference['Authors'] = 'S.M Dunlop'
                if reference['Authors'] == 'P. Lloyd; E.E. Plaganyi; S.J. Weeks; M.A.R.I.T.E.S. MAGNO-CANTO; G. Plaganyi':
                    reference['Authors'] = 'P. Lloyd; E.E. Plaganyi; S.J. Weeks; M. Magno-Canto; G. Plaganyi'
                if reference['Authors'] == 'I. Chen; P.E.I.F.E.N. LEE; W.A.N.N.N.I.A.N. TZENG;':
                    reference['Authors'] = 'I. Chen; P. Lee; W. Tszeng'
                if reference['Authors'] == 'D.A.V.I.D.B. McCLELLAN; N.A.N.C.I.E.J. Cummings':
                    reference['Authors'] = 'D.B. McClellan; N.J. Cummings'
                reference['Authors'] = reference['Authors'].replace('A.L.B.R.E.C.H.T. GOeTZ;', 'A. Goetz;')
                regex = r'((?:[A-Z]\.)+)\s+([^;]+)(?:;|$)'
                matches = re.findall(regex, reference['Authors'])
                authors = []
                for m in matches:
                    try:
                        surname = m[1].strip()
                        initials = m[0].replace('.', '').strip()
                    except:
                        import pdb; pdb.set_trace()

                    # Try and get all possible people in the database first
                    p = people_models.Person.objects.filter(surname=surname, initials=initials).first()

                    # If there's nobody there then try get same surname and no initials, it's probably the same person
                    # Someone can split it out later manually if it's not
                    if p is None:
                        p = people_models.Person.objects.filter(surname=surname, initials__isnull=True,
                                                                initials__exact='').first()
                        if p is None:
                            # Otherwise if we can't find anyone with the same surname make a new person
                            p = people_models.Person(surname=surname, initials=initials)
                        else:
                            p.initials = initials
                        p.save()

                        authors.append(p)

                author_string = [x.surname + " " + x.initials for x in authors]
                author_string = ' and '.join(author_string)
                bibtex_dict = {'year': str(reference['Year of Publication']),
                               'title': imports_views.fix_case(reference['Title']),
                               'author': author_string,
                               'ENTRYTYPE': type,
                               'ID': reference['Nid']}

                # Iterate over all of the fields for a reference, convert them to the bibtex title then add them
                for key, value in enumerate(ref_field_mapper):
                    if key in reference and reference[key].strip() != '':
                        bibtex_dict[value] = reference[key]

                # Access date alwyas seems to be blank
                #if 'Access Date' in reference and reference['Access Date'].strip() != '':
                #    bibtex_dict['note'] = '{Accessed: ' +

                if 'Pagination' in reference and reference['Pagination'].strip() != '':
                    bibtex_dict['pages'] = reference['Pagination'].replace('–', '--').replace('-', '--').replace(' ', '')
                if 'Secondary Title' in reference and reference['Secondary Title'].strip() != '':
                    reference['Secondary Title'] = imports_views.fix_case(reference['Secondary Title'])
                    if type == 'article':
                        bibtex_dict['journal'] = reference['Secondary Title'].strip()
                    elif type == 'bookchapter':
                        bibtex_dict['booktitle'] = bibtex_dict['title']
                        bibtex_dict['title'] = reference['Secondary Title'].strip()
                    elif type == 'inproceedings' or type == 'proceedings':
                        bibtex_dict['series'] = reference['Secondary Title'].strip()

                # Create and save the reference object
                year = bibtex_dict['year'].strip() if bibtex_dict['year'].lower() != 'in press' else 2017
                ref = biblio_models.Reference(year=int(year),
                                              title=bibtex_dict['title'],
                                              bibtex=bibtex_dict)
                ref.save()

                # Assign authors to the reference
                biblio_models.assign_multiple_authors(authors, ref)

                # Associate with the assessment
                assessment.references.add(ref)

        if row['Images'].strip():
            image_counter = 1
            for img in row['Images'].split(','):
                img_nid = img.strip()
                if img_nid:
                    img_directory = os.path.join(settings.BASE_DIR, 'website', 'static', 'sp-imgs')

                    # Work out if the local file already exists on the server
                    new_file_name = parent.name.lower().replace(' ', '_') + '_' + str(image_counter) + '.jpg'
                    image_counter += 1
                    local_img_path = os.path.join(img_directory, new_file_name)
                    if os.path.exists(local_img_path):
                        continue

                    # If it doesn't, go and fetch it remotely
                    img_metadata = images[img_nid]
                    file_name = img_metadata['Image'].strip()
                    file_name = file_name.replace('ï', 'i')
                    file_name = file_name.replace('.png', '.jpg')
                    remote_img_path = os.path.join(pwd, 'seakey-images', file_name)
                    if os.path.exists(remote_img_path):
                        shutil.copy(remote_img_path, img_directory)
                        os.rename(os.path.join(img_directory, file_name), os.path.join(img_directory, new_file_name))
                    else:
                        import pdb; pdb.set_trace()
                    # path = 'http://seakeys.sanbi.org/sites/default/files/seakey-images/'
                    # remote_file = urlopen(path + file_name)
                    # with open(local_img_path, 'wb') as local_file:
                    #    shutil.copyfileobj(remote_file, local_file)

                    # Add the exif info into it
                    try:
                        print(subprocess.check_output(['exiftool', '-IPTC:By-line=' + img_metadata['Author'],
                                                   '-IPTC:CopyrightNotice=' + img_metadata['Copyright notice'],
                                                   '-IPTC:Source=Seakeys', '-overwrite_original', local_img_path]))
                    except:
                        import pdb; pdb.set_trace()
                    # new_image = models.Image(taxon=parent, url=url)
                    # new_image.save()

        if row['Common names'].strip():
            for name in row['Common names'].split(','):
                name = name.strip()
                if name:
                    english, created = models.Language.objects.get_or_create(name='English')

                    # Use get or create so we don't add same common name twice
                    models.CommonName.objects.get_or_create(language=english, taxon=parent, name=name)

