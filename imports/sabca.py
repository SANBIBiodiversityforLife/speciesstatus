
from django.shortcuts import render
from taxa import models
from biblio import models as biblio_models
from people import models as people_models
from redlist import models as redlist_models
from suds.client import Client
import requests
from mendeley import Mendeley
import re
from django.db.models import Count
from django.http import HttpResponse
import pandas as pd
import pypyodbc
from psycopg2.extras import NumericRange
from imports import views as imports_views
import datetime
from django.contrib.gis.geos import Point
import re


def import_sabca_sql():
    mendeley_id = '3513'
    mendeley_secret = 'gOVvM5RmKseDgcmH'
    mendeley_redirect = 'http://species.sanbi.org'
    mendeley = Mendeley(mendeley_id, client_secret=mendeley_secret, redirect_uri=mendeley_redirect)
    mendeley_session = mendeley.start_client_credentials_flow().authenticate()


    conn = pypyodbc.connect("Driver={SQL Server};Server=CPTDSK0118\SQLEXPRESS;Trusted_Connection=ye‌​s;database=sabca")
    dql =  pypyodbc.connect("Driver={SQL Server};Server=CPTDSK0118\SQLEXPRESS;Trusted_Connection=ye‌​s;database=sabca-sanbi")
    cons_sql = """SELECT sp_code, item_text
FROM asmt_vocabulary vocab
JOIN asmt_conservation_measure cons
ON vocab.Item_order = cons.Measure_code
WHERE vocab.Keyword = 'conservation_measures';"""

    ppl_sql = """SELECT sp_code
		,Author1 AS name
		,Author2 AS name2
	FROM asmt_data"""
    taxa_sql = """SELECT *
	FROM vm_taxonomy"""
    bib_sql = """SELECT link.sp_code
		,authors
		,year
		,title
		,Journal
		,book_title
		,editors
		,issue
		,page
		,publisher
		,pub_locality
		,keywords
		,url
FROM asmt_bibliography AS biblio
JOIN asmt_bibliography_link AS link
ON biblio.Bib_code = link.Bib_code"""
    dist = """
    SELECT sp_code,
Institution_code+'|'+Collection_code AS origin_code,
collector,
Decimal_latitude AS lat,
Decimal_longitude AS "long",
Coords_uncertainty_description AS uncert,
Locus AS locus,
year_collected AS year,
Month_collected AS month,
Day_collected AS day
FROM vm_data;"""
    criteria = """SELECT [sp_code]
              ,[rl_A1a]
              ,[rl_A1b]
              ,[rl_A1c]
              ,[rl_A1d]
              ,[rl_A1e]
              ,[rl_A2a]
              ,[rl_A2b]
              ,[rl_A2c]
              ,[rl_A2d]
              ,[rl_A2e]
              ,[rl_A3b]
              ,[rl_A3c]
              ,[rl_A3d]
              ,[rl_A3e]
              ,[rl_A4a]
              ,[rl_A4b]
              ,[rl_A4c]
              ,[rl_A4d]
              ,[rl_A4e]
              ,[rl_B1a]
              ,[rl_B1b_i]
              ,[rl_B1b_ii]
              ,[rl_B1b_iii]
              ,[rl_B1b_iv]
              ,[rl_B1b_v]
              ,[rl_B1c_i]
              ,[rl_B1c_ii]
              ,[rl_B1c_iii]
              ,[rl_B1c_iv]
              ,[rl_B2a]
              ,[rl_B2b_i]
              ,[rl_B2b_ii]
              ,[rl_B2b_iii]
              ,[rl_B2b_iv]
              ,[rl_B2b_v]
              ,[rl_B2c_i]
              ,[rl_B2c_ii]
              ,[rl_B2c_iii]
              ,[rl_B2c_iv]
              ,[rl_C1]
              ,[rl_C2a_i]
              ,[rl_C2a_ii]
              ,[rl_C2b]
              ,[rl_D]
              ,[rl_D1]
              ,[rl_D2]
              ,[rl_E]
          FROM [sabca].[dbo].[asmt_data] WHERE rl_Category <> '';"""
    d = pd.read_sql(dist, dql)
    d.columns = map(str.lower, d.columns)
    t = pd.read_sql(taxa_sql, conn)
    t.columns = map(str.lower, t.columns)
    cn = pd.read_sql("SELECT * FROM asmt_common_names;", conn)
    cn.columns = map(str.lower, cn.columns)
    ppl = pd.read_sql(ppl_sql, conn)
    ppl.columns = map(str.lower, ppl.columns)
    assess = pd.read_sql("SELECT * FROM asmt_data WHERE rl_category <> '';", conn)
    assess.columns = map(str.lower, assess.columns)
    biblio = pd.read_sql(bib_sql, conn)
    biblio.columns = map(str.lower, biblio.columns)
    cons_actions = pd.read_sql(cons_sql, conn)
    cons_actions.columns = map(str.lower, cons_actions.columns)
    cr = pd.read_sql(criteria,conn)



    exclude_from_assessment = [
         'sys_Habitat'
        ,'special_Population_blog'
        ,'Range'
        ,'aoo2'
        ,'eoo2'
        ,'rl_category'
        ,'rl_rationale'
        ,'sp_code'
    ]

    ppl[['firstname', 'initials', 'surname']] = ppl['name'].str.extract(
        r'^([A-Za-z]+)\s+([A-Za-z\.]+)\s+([A-Za-z]+$)', expand=True)
    temp = ppl.loc[pd.isnull(ppl['firstname']), 'name'].str.extract(r'^([A-Za-z]+)\s+([A-Za-z]+$)', expand=True)
    ppl.loc[pd.isnull(ppl['firstname']), 'firstname'] = temp[0]
    ppl.loc[pd.isnull(ppl['surname']), 'surname'] = temp[1]

    # Author 2
    ppl[['firstname1', 'initials1', 'surname1']] = ppl['name2'].str.extract(
        r'^([A-Za-z]+)\s+([A-Za-z\.]+)\s+([A-Za-z]+$)', expand=True)
    temp = ppl.loc[pd.isnull(ppl['firstname1']), 'name2'].str.extract(r'^([A-Za-z]+)\s+([A-Za-z]+$)', expand=True)
    ppl.loc[pd.isnull(ppl['firstname1']), 'firstname1'] = temp[0]

    ppl.loc[pd.isnull(ppl['surname1']), 'surname1'] = temp[1]


    biblio['type'] = ''
    #import pdb; pdb.set_trace()
    biblio.loc[(biblio['journal'] == '') & (biblio['book_title'] == '') & (biblio['year'] != ''), ['type']] = 'misc'
    biblio.loc[(biblio['journal'] == '') & (biblio['book_title'] == '') & (biblio['year'] != '') & (
    biblio['publisher'] != ''), ['type']] = 'techreport'
    biblio.loc[(biblio['journal'] == '') & (biblio['book_title'] != '') & (biblio['year'] != '') & (
        biblio['title'] != ''), ['type']] = 'inbook'
    biblio.loc[(biblio['journal'] == '') & (biblio['book_title'] != '') & (biblio['year'] != '') & (
        biblio['title'] == ''), ['type']] = 'book'
    biblio.loc[(biblio['journal'] != '') & (biblio['year'] != ''), ['type']] = 'article'

    redlist_cat_mapping = {
        'regionally extinct': redlist_models.Assessment.EXTINCT,
        'extinct': redlist_models.Assessment.EXTINCT,
        'critically endangered': redlist_models.Assessment.CRITICALLY_ENDANGERED,
        'endangered': redlist_models.Assessment.ENDANGERED,
        'vulnerable': redlist_models.Assessment.VULNERABLE,
        'near threatened': redlist_models.Assessment.NEAR_THREATENED,
        'least concern': redlist_models.Assessment.LEAST_CONCERN,
        'data deficient': redlist_models.Assessment.DATA_DEFICIENT,
        'not listed': redlist_models.Assessment.NOT_EVALUATED,
        'not set': redlist_models.Assessment.NOT_EVALUATED,
        'not assessed': redlist_models.Assessment.NOT_EVALUATED,
    }
    scope_mapping={
        'Regional': redlist_models.Assessment.REGIONAL,
        'Global': redlist_models.Assessment.GLOBAL
    }
    # Iterate through the allfields table, 1 row represents 1 assessment for a taxon

    def test(row):
        cats = []
        for index, item in enumerate(row):
            if item != 0 and index != 0:
                cats.append(item)
        return '|'.join(cats)


    p = cr.loc[:, ].replace(1, pd.Series(cr.columns, cr.columns))
    #k = p.reindex_axis(['sp_code'] + list(p.columns[:-1]), axis=1)
    temp_cr = p.apply(test, axis=1)
    assess['criteria'] = temp_cr



    for index, row in assess.iterrows():
        # Retrieve the taxon info for the assessment we're on
        taxon_row = t.loc[t['sp_code'] == row['sp_code']]

        taxon_row = {k: v.iloc[0] for k, v in taxon_row.items() if pd.notnull(v.iloc[0])}
        try:
            species, created = create_taxon_from_sarca_sabca(taxon_row, mendeley_session)
        except:
            import pdb;
            pdb.set_trace()
        if not created:
            print('Taxon created already')
            continue

        if created:
            # Add common names and languages for the taxon
            try:
                common_names = cn.loc[cn['sp_code'] == row['sp_code']]
            except:
                import pdb; pdb.set_trace()
            for ind, cns in common_names.iterrows():
                language, created = models.Language.objects.get_or_create(name=cns['language'])
                models.CommonName.objects.get_or_create(language=language, name=cns['common_name'], taxon=species)

            # Remove all row columns which do not contain info
            row = {k: v for k, v in row.items() if pd.notnull(v) and v != ''}
            # All species objects should have a corresponding info object, so let's create one
            info = models.Info(taxon=species)

            # Get the taxon info stuff from the assessment csv and save it
            assess_row = assess.loc[assess['sp_code'] == row['sp_code']]

            #for k, v in assess_row.items():
            #    import pdb; pdb.set_trace()
            assess_row = {k: v.iloc[0] for k, v in assess_row.items() if pd.notnull(v.iloc[0]) and v.iloc[0] != ''}
            info.habitat_narrative = ''
            if 'sys_terrestrial' in assess_row:
                if assess_row['sys_terrestrial'] == 1:
                    info.habitat_narrative = '<p class="system">Terrestrial</p>'
            if 'sys_habitat' in assess_row:
                info.habitat_narrative += assess_row['sys_habitat']
            info.save()

            # Add habitats
            a = redlist_models.Assessment(
                taxon=species, date=datetime.date(2013, 1, 1)
            )

            a.distribution_narrative = ''
            if 'range' in assess_row:
                a.distribution_narrative = assess_row['range']
            temp = {'Area of occupancy': 'aoo2_notes',
                    'Extent of occurrence': 'eoo2_notes'}
            for key, value in temp.items():
                if value in row:
                    a.distribution_narrative += '<h3>' + key + '</h3><div>' + row[value] + '</div>'

            if 'special_threats_text' in assess_row:
                a.threats_narrative = assess_row['special_threats_text']

            if 'special_population_trend' in assess_row:
                a.population_trend = assess_row['special_population_trend']
            if 'special_population_blog' in assess_row:
                a.population_trend_narrative = assess_row['special_population_blog']
            if 'sys_cons_measures' in assess_row:
                a.conservation_narrative = assess_row['sys_cons_measures']
            if 'scope' in assess_row:
                a.scope = scope_mapping[assess_row['scope'].capitalize()]
            if 'criteria' in assess_row:
                a.redlist_criteria = assess_row['criteria'].replace('rl_', '')
            if 'aoo2' in row:
                aoo = re.sub('[^0-9]', '',row['aoo2'])
                a.area_occupancy = NumericRange(int(aoo), int(int(aoo)))
            if 'eoo2' in row:
                eoo = re.sub('[^0-9]', '', row['eoo2'])
                a.extent_occurrence = NumericRange(int(eoo), int(eoo))
            if 'rl_category' in assess_row:
                a.redlist_category = redlist_cat_mapping[assess_row['rl_category'].lower()]
            if 'rl_rationale_ms' in assess_row:
                a.rationale = assess_row['rl_rationale_ms']

            # Convert all of the other columns data into json and stick it in the temp hstore field
            # There is SO much info and no way to structure it, best if someone goes and pulls it out manually
            # as and when they need it
            #hstore_values = {k: v for k, v in row.items() if k not in exclude_from_assessment}
            #a.temp_field = hstore_values

            # Save the assessment object now everything has been added to it above
            #import pdb; pdb.set_trace()
            try:
                a.save()
            except:
                import pdb
                pdb.set_trace()
                print(taxon_row)
                continue




            ref_rows = biblio.loc[biblio['sp_code'] == row['sp_code']]
            for i, r in ref_rows.iterrows():
                authors = imports_views.create_authors(r['authors'])
                author_string = [x.surname + " " + x.initials for x in authors]
                author_string = ' and '.join(author_string)

                # Sometimes these idiots didn't enter a year, in which case I am throwing the whole reference out
                if pd.isnull(r['year']):
                    print(r['year'])
                    continue

                # For the year you sometimes have 1981b for example, so just get first 4 chars
                if str(r['year']).startswith('In'):
                    continue
                elif r['year'] == '':
                    continue
                elif r['title'] == '' or pd.isnull(r['title']) or r['title'] is None:
                    continue
                else:
                    bibtex_dict = {'year': str(r['year'])[:4],
                                'title': r['title'],
                                'author': author_string}
                # Fuck I don't understand why people try to make bibliographic data relational, it's a headache
                # When there's a perfectly good language designed to hold and express it - bibtex
                # I am sticking it all in a dictionary apart from title, year and authors, and use bibtexparser to convert
                # Now I have to add this and that depending on type. FML. Going to get rid of all empty stuff first
                # See http://www.openoffice.org/bibliographic/bibtex-defs.html for list of relevant bibtex fields
                r = {k: v for k, v in r.items() if pd.notnull(v) and v != ''}
                # thesis and dissertations, reports

                r['type'] = r['type'].lower()
                if r['type'] == 'article':
                    bibtex_dict['ENTRYTYPE'] = 'article'
                    if 'title' in r:
                        bibtex_dict['title'] = r['title']
                    if 'journal' in r:
                        bibtex_dict['journal'] = r['journal']
                    if 'editors' in r:
                        bibtex_dict['editor'] = r['editors']
                    if 'page' in r:
                        bibtex_dict['pages'] = r['page'].replace('-', '--') # Apparently this is what bibtex wants
                    if 'issue' in r:
                        bibtex_dict['number'] = r['issue']
                    if 'publisher' in r:
                        bibtex_dict['publisher'] = r['publisher']
                    if 'pub_locality' in r:
                        bibtex_dict['address'] = r['pub_locality']
                elif r['type'] == 'book':
                    bibtex_dict['ENTRYTYPE'] = 'book'
                    if 'editors' in r:
                        bibtex_dict['editor'] = r['editors']
                    if 'title' in r:
                        bibtex_dict['title'] = r['title']
                    if 'pub_locality' in r:
                        bibtex_dict['address'] = r['pub_locality']
                    if 'publisher' in r:
                        bibtex_dict['publisher'] = r['publisher']
                    if 'page' in r:
                        bibtex_dict['pages'] = r['page'].replace('-', '--')

                    # We have to do some extra things for book chapters
                elif r['type'] == 'inbook':
                    bibtex_dict['ENTRYTYPE'] = 'inbook'
                    if 'editors' in r:
                        bibtex_dict['editor'] = r['editors']
                    if 'pub_locality' in r:
                        bibtex_dict['address'] = r['pub_locality']
                    if 'publisher' in r:
                        bibtex_dict['publisher'] = r['publisher']
                    if 'page' in r:
                        bibtex_dict['pages'] = r['page'].replace('-', '--')
                    if 'title' in r:
                        bibtex_dict['title'] = r['title'] # This is the chapter's title. ARGH.
                    if 'book_title' in r:
                        bibtex_dict['booktitle'] = r['book_title']
                elif r['type'] == 'techreport' or r['type'] == 'misc':
                    if r['type'] == 'techreport':
                        bibtex_dict['ENTRYTYPE'] = 'techreport'
                    if r['type'] == 'misc':
                        bibtex_dict['ENTRYTYPE'] = 'misc'
                    if 'publisher' in r:
                        bibtex_dict['institution'] = r['publisher']
                    if 'title' in r:
                        bibtex_dict['title'] = r['title']
                else:
                    print(r)
                    import pdb; pdb.set_trace() # It's some type we haven't thought of yet

                # from bibtexparser.bwriter import BibTexWriter; from bibtexparser.bibdatabase import BibDatabase
                # db = BibDatabase(); db.entries = [bibtex_dict]; writer = BibTexWriter(); writer.write(db)
                # Required for bibtexparser, just putting in a random number for now
                bibtex_dict['ID'] = str(row['sp_code'])

                # Create and save the reference object
                ref = biblio_models.Reference(year=int(bibtex_dict['year']),
                                              title=bibtex_dict['title'],
                                              bibtex=bibtex_dict)
                try:
                    ref.save()
                except:
                    import pdb; pdb.set_trace()

                # Assign authors to the reference
                biblio_models.assign_multiple_authors(authors, ref)
                assessment = a

                # Associate with the assessment
                assessment.references.add(ref)

            # Add Conservation actions
            cons_rows = cons_actions.loc[cons_actions['sp_code'] == row['sp_code']]
            for i, c in cons_rows.iterrows():
                # The conservation actions csv contains lots of codes like 3.1.1, we need to look them up

                action_name = c['item_text'].strip()
                try:
                    action, created = redlist_models.Action.objects.get_or_create(name=action_name,
                                                                     action_type=redlist_models.Action.CONSERVATION)
                    action_nature = redlist_models.ActionNature.objects.create(assessment=a, action=action)
                except:
                    import pdb; pdb.set_trace()

            # Get a list of all contributors/assessors/whatevers for the assessment
            ppl_ = ppl.loc[ppl['sp_code'] == row['sp_code']]
            # people_rows.sort_values(['lastName', 'firstName'], inplace=True)
            for i, p in ppl_.iterrows():
                author1, created = people_models.Person.objects.get_or_create(first=p['firstname'], surname=p['surname'])
                if created:
                    #person.email = p['email']
                    author1.initials = p['initials']
                    author1.save()

                # Add the person as an assessor or contributor to the database
                c = redlist_models.Contribution.objects.create(person=author1,
                                                               assessment=a,
                                                               type='A',
                                                               weight=1)
                c.save()

                if (p['surname1'] != '') & (pd.notnull(p['surname1'])):
                    author2, created = people_models.Person.objects.get_or_create(first=p['firstname1'], surname=p['surname1'])
                    if created:
                        #person.email = p['email']
                        author2.initials = p['initials1']
                        author2.save()

                    # Add the person as an assessor or contributor to the database
                    c = redlist_models.Contribution.objects.create(person=author2,
                                                                   assessment=a,
                                                                   type='A',
                                                                   weight=2)
                    c.save()

            dist = d.loc[d['sp_code'] == row['sp_code']]
            for i, occur in dist.iterrows():
                occur = {k: v for k, v in occur.items() if pd.notnull(v)}
                if 'long' in occur and 'lat' in occur:
                    point = models.PointDistribution(taxon=species, point=Point(occur['long'], occur['lat']))
                    if 'year' in occur:
                        day = occur['day'] if 'day' in occur else 1
                        month = occur['month'] if 'month' in occur else 1
                        try:
                            point.date = datetime.date(int(occur['year']), int(month), int(day))
                        except:
                            point.date = datetime.date(int(occur['year']), (int(month)+1), 1)
                    # if 'collector' in occur:
                    #     import pdb; pdb.set_trace()
                    #     person = imports_views.create_authors(occur['collector'])[0]
                    #     point.collector = person
                    if 'locus' in occur:
                        point.qds = occur['locus']
                    if 'origin_code' in occur:
                        point.origin_code = str(occur['origin_code'])[:8]

                    point.save()


    print('done')
    import pdb
    pdb.set_trace()

    return HttpResponse('<html><body><p>Done</p></body></html>')


def create_taxon_from_sarca_sabca(row, mendeley_session):
    """
    Adds to the taxa hierarchy from vm_taxonomy
    :param row:
    :return:
    """
    # Preset the Animalia Kingdom as parent ready for the for loop below
    kingdom_rank = models.Rank.objects.get(name='Kingdom')
    parent = models.Taxon.objects.get(name='Animalia', rank=kingdom_rank)

    # Make a list of the taxa hierarchy from the SIS row in the csv to iterate over
    taxa_hierarchy = [
        ['phylum', row['phylum']],
        ['class', row['class']],
        ['order', row['order_']],
        ['suborder', row['suborder']],
        ['superfamily', row['superfamily']],
        ['family', row['family']],
        ['subfamily', row['subfamily']],
        ['genus', row['genus']],
    ]
    for t in taxa_hierarchy:
        if t[1] != '':
            rank, created = models.Rank.objects.get_or_create(name=t[0].capitalize())
            #taxon_name = t[1].strip().capitalize()
            taxon_name = t[1]
            parent, created = models.Taxon.objects.get_or_create(parent=parent, name=taxon_name, rank=rank)

    # Finally add the species to the taxa hierarchy - sometimes this thing only goes go genus level so put it in an if
    if 'scientific_name' in row:
        rank = models.Rank.objects.get(name='Species')
        species_name = row['scientific_name'].strip()
        species, created = models.Taxon.objects.get_or_create(parent=parent, name=species_name, rank=rank)
    else:
        species = parent

    if 'subspecies' in row and row['subspecies'] != '':
        rank, created = models.Rank.objects.get_or_create(name='Subspecies')
        species_name = parent.name + ' ' + row['subspecies'].strip()
        species, created = models.Taxon.objects.get_or_create(parent=parent, name=species_name, rank=rank)

    if not created:
        print('species already exists in db')
    else:
        if 'taxonomic_notes' in row:
            # Add taxon notes if there are any
            taxon_notes = row['taxonomic_notes']
            #import pdb; pdb.set_trace()
            if taxon_notes is not None and taxon_notes != '':
                species.notes = taxon_notes
                species.save()

        # Create a description and set of references
        if 'taxonomic_authority' in row:
            imports_views.create_taxon_description(row['taxonomic_authority'], species, mendeley_session)

    return species, created
