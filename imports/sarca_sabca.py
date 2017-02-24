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
import pymysql
from psycopg2.extras import NumericRange
from imports import views as imports_views
import datetime

def import_sql():
    mendeley_id = '3513'
    mendeley_secret = 'gOVvM5RmKseDgcmH'
    mendeley_redirect = 'http://species.sanbi.org'
    mendeley = Mendeley(mendeley_id, client_secret=mendeley_secret, redirect_uri=mendeley_redirect)
    mendeley_session = mendeley.start_client_credentials_flow().authenticate()


    conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db='sarca')
    dql =  pymysql.connect(host='localhost', port=3306, user='root', passwd='', db='sarca_sanbi')
    cons_sql = """SELECT Sp_code, Item_text
FROM asmt_vocabulary vocab
JOIN asmt_conservation_measure cons
ON vocab.Item_order = cons.Measure_code
WHERE vocab.Keyword = 'conservation_measures';"""
    sql = """SELECT
    Sp_code
    ,CASE WHEN rl_A1a = 1 THEN 'A1a' END as A1a
    ,CASE WHEN rl_A1b = 1 THEN 'A1b' END as A1b
    ,CASE WHEN rl_A1c = 1 THEN 'A1c' END as A1c
    ,CASE WHEN rl_A1d = 1 THEN 'A1d' END as A1d
    ,CASE WHEN rl_A1e = 1 THEN 'A1e' END as A1e
    ,CASE WHEN rl_A2a = 1 THEN 'A2a' END as A2a
    ,CASE WHEN rl_A2b = 1 THEN 'A2b' END as A2b
    ,CASE WHEN rl_A2c = 1 THEN 'A2c' END as A2c
    ,CASE WHEN rl_A2d = 1 THEN 'A2d' END as A2d
    ,CASE WHEN rl_A2e = 1 THEN 'A2e' END as A2e
    ,CASE WHEN rl_A3b = 1 THEN 'A3b' END as A3b
    ,CASE WHEN rl_A3c = 1 THEN 'A3c' END as A3c
    ,CASE WHEN rl_A3d = 1 THEN 'A3d' END as A3d
    ,CASE WHEN rl_A3e = 1 THEN 'A3e' END as A3e
    ,CASE WHEN rl_A4a = 1 THEN 'A4a' END as A4a
    ,CASE WHEN rl_A4b = 1 THEN 'A4b' END as A4b
    ,CASE WHEN rl_A4c = 1 THEN 'A4c' END as A4c
    ,CASE WHEN rl_A4d = 1 THEN 'A4d' END as A4d
    ,CASE WHEN rl_A4e = 1 THEN 'A4e' END as A4e
    ,CASE WHEN rl_B1a = 1 THEN 'B1a' END as B1a
    ,CASE WHEN rl_B1b_i = 1 THEN 'B1b(i)' END as B1b_i
    ,CASE WHEN rl_B1b_ii = 1 THEN 'B1b(ii)' END as B1b_ii
    ,CASE WHEN 'rl_B1b_iii' = 1 THEN 'B1b(iii)'END AS B1b_iii
    ,CASE WHEN 'rl_B1b_iv' = 1 THEN 'B1b(iv)'END AS B1b_iv
    ,CASE WHEN 'rl_B1b_v' = 1 THEN 'B1b(v)'END AS B1b_v
    ,CASE WHEN 'rl_B1c_i' = 1 THEN 'B1c(i)'END AS B1c_i
    ,CASE WHEN 'rl_B1c_ii' = 1 THEN 'B1c(ii)'END AS B1c_ii
    ,CASE WHEN 'rl_B1c_iii' = 1 THEN 'B1c(iii)'END AS B1c_iii
    ,CASE WHEN 'rl_B1c_iv' = 1 THEN 'B1c(iv)'END AS B1c_iv
    ,CASE WHEN 'rl_B2a' = 1 THEN 'B2a'END AS B2a
    ,CASE WHEN 'rl_B2b_i' = 1 THEN 'B2b(i)'END AS B2b_i
    ,CASE WHEN 'rl_B2b_ii' = 1 THEN 'B2b(ii)'END AS B2b_ii
    ,CASE WHEN 'rl_B2b_iii' = 1 THEN 'B2b(iii)'END AS B2b_iii
    ,CASE WHEN 'rl_B2b_iv' = 1 THEN 'B2b(iv)'END AS B2b_iv
    ,CASE WHEN 'rl_B2b_v' = 1 THEN 'B2b(v)'END AS B2b_v
    ,CASE WHEN 'rl_B2c_i' = 1 THEN 'B2c(i)'END AS B2c_i
    ,CASE WHEN 'rl_B2c_ii' = 1 THEN 'B2c(ii)'END AS B2c_ii
    ,CASE WHEN 'rl_B2c_iii' = 1 THEN 'B2c(iii)'END AS B2c_iii
    ,CASE WHEN 'rl_B2c_iv' = 1 THEN 'B2c(iv)'END AS B2c_iv
    ,CASE WHEN 'rl_C1' = 1 THEN 'C1'END AS C1
    ,CASE WHEN 'rl_C2a_i' = 1 THEN 'C2a(i)'END AS C2a_i
    ,CASE WHEN 'rl_C2a_ii' = 1 THEN 'C2a(ii)'END AS C2a_ii
    ,CASE WHEN 'rl_C2b' = 1 THEN 'C2b'END AS C2b
    ,CASE WHEN 'rl_D' = 1 THEN 'D'END AS D
    ,CASE WHEN 'rl_D1' = 1 THEN 'D1'END AS D1
    ,CASE WHEN 'rl_D2' = 1 THEN 'D2'END AS D2
    ,CASE WHEN 'rl_E' = 1 THEN 'E'END AS E
    FROM asmt_data"""
    ppl_sql = """SELECT Sp_code
		,Author1 AS name
		,Author2 AS name2
	FROM sarca.asmt_data"""
    taxa_sql = """SELECT *
	FROM sarca.vm_taxonomy"""
    bib_sql = """SELECT link.Sp_code
		,Authors
		,Year
		,Title
		,Journal
		,Book_title
		,Editors
		,Issue
		,Page
		,Publisher
		,Pub_locality
		,Keywords
		,url
FROM asmt_bibliography AS biblio
JOIN asmt_bibliography_link AS link
ON biblio.Bib_code = link.Bib_code"""
    dist = """
    SELECT Sp_code,
Institution_code+'|'+Collection_code AS origin_code,
collector,
Decimal_latitude AS lat,
Decimal_longitude AS "long",
Coords_uncertainty_description AS uncert,
Locus AS locus,
Year_collected AS year,
Month_collected AS month,
Day_collected AS day
FROM sarca_sanbi.vm_data;"""

    d = pd.read_sql(dist, dql)

    criteria = pd.read_sql(sql, conn)
    t = pd.read_sql(taxa_sql, conn)
    cn = pd.read_sql("SELECT * FROM sarca.asmt_common_names;", conn)
    ppl = pd.read_sql(ppl_sql, conn)
    assess = pd.read_sql("SELECT * FROM sarca.asmt_data WHERE rl_Category <> '';", conn)
    biblio = pd.read_sql(bib_sql, conn)
    cons_actions = pd.read_sql(cons_sql, conn)

    exclude_from_assessment = [
         'sys_Habitat'
        ,'special_Population_blog'
        ,'Range'
        ,'AOO2'
        ,'EOO2'
        ,'rl_Category'
        ,'rl_Rationale'
        ,'Sp_code'
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
    biblio.loc[(biblio['Journal'] == '') & (biblio['Book_title'] == '') & (biblio['Year'] != ''), ['type']] = 'misc'
    biblio.loc[(biblio['Journal'] == '') & (biblio['Book_title'] == '') & (biblio['Year'] != '') & (
    biblio['Publisher'] != ''), ['type']] = 'techreport'
    biblio.loc[(biblio['Journal'] == '') & (biblio['Book_title'] != '') & (biblio['Year'] != '') & (
        biblio['Title'] != ''), ['type']] = 'inbook'
    biblio.loc[(biblio['Journal'] == '') & (biblio['Book_title'] != '') & (biblio['Year'] != '') & (
        biblio['Title'] == ''), ['type']] = 'book'
    biblio.loc[(biblio['Journal'] != '') & (biblio['Year'] != ''), ['type']] = 'article'

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

    # Iterate through the allfields table, 1 row represents 1 assessment for a taxon
    def test(row):
        cats = []
        for index, item in enumerate(row):
            if item is not None and item != 'None' and index != 0:
                cats.append(item)

        return '|'.join(cats)

    temp = criteria.apply(test, axis=1)
    criteria['criteria'] = temp

    for index, row in assess.iterrows():
        # Retrieve the taxon info for the assessment we're on
        taxon_row = t.loc[t['Sp_code'] == row['Sp_code']]
        taxon_row = {k: v.iloc[0] for k, v in taxon_row.items() if pd.notnull(v.iloc[0])}
        species, created = create_taxon_from_sarca_sabca(taxon_row, mendeley_session)
        if not created:
            print('Taxon created already')
            continue
        # Add common names and languages for the taxon
        try:
            common_names = cn.loc[cn['Sp_code'] == row['Sp_code']]
        except:
            import pdb; pdb.set_trace()
        for ind, cns in common_names.iterrows():
            language, created = models.Language.objects.get_or_create(name=cns['Language'])
            models.CommonName.objects.get_or_create(language=language, name=cns['Common_name'], taxon=species)

        # Remove all row columns which do not contain info
        row = {k: v for k, v in row.items() if pd.notnull(v)}
        # All species objects should have a corresponding info object, so let's create one
        info = models.Info(taxon=species)

        # Get the taxon info stuff from the assessment csv and save it
        assess_row = assess.loc[assess['Sp_code'] == row['Sp_code']]

        #for k, v in assess_row.items():
        #    import pdb; pdb.set_trace()
        assess_row = {k: v.iloc[0] for k, v in assess_row.items() if pd.notnull(v.iloc[0])}

        if 'sys_Habitat' in assess_row:
            info.habitat_narrative = assess_row['sys_Habitat']
        if 'special_Population_blog' in assess_row:
            info.population_trend_narrative = assess_row['special_Population_blog']
        if 'Range' in assess_row:
            info.distribution = assess_row['Range']

        info.save()

        # Add habitats

        a = redlist_models.Assessment(
            taxon=species, date= datetime.date(2016, 2, 1)
        )

        criteria = criteria.loc[criteria['Sp_code'] == row['Sp_code'], 'criteria']
        if criteria is not None:
            a.redlist_criteria = criteria
        if 'AOO2' in row:
            a.area_occupancy = NumericRange(int(row['AOO2']), int(row['AOO2']))
        if 'EOO2' in row:
            a.extent_occurrence = NumericRange(int(row['EOO2']), int(row['EOO2']))
        if 'rl_Category' in assess_row:
            a.redlist_category = redlist_cat_mapping[assess_row['rl_Category'].lower()]
        if 'rl_Rationale' in assess_row:
            a.rationale = assess_row['rl_Rationale']

        # Convert all of the other columns data into json and stick it in the temp hstore field
        # There is SO much info and no way to structure it, best if someone goes and pulls it out manually
        # as and when they need it
        hstore_values = {k: v for k, v in row.items() if k not in exclude_from_assessment}
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




        ref_rows = biblio.loc[biblio['Sp_code'] == row['Sp_code']]
        for i, r in ref_rows.iterrows():
            authors = imports_views.create_authors(r['Authors'])
            author_string = [x.surname + " " + x.initials for x in authors]
            author_string = ' and '.join(author_string)

            # Sometimes these idiots didn't enter a year, in which case I am throwing the whole reference out
            if pd.isnull(r['Year']):
                print(r['Year'])
                continue

            # For the year you sometimes have 1981b for example, so just get first 4 chars
            if str(r['Year']).startswith('In'):
                continue
            elif r['Year'] == '':
                continue
            elif r['Title'] == '' or pd.notnull(r['Title']) or r['Title'] is None:
                continue
            else:
                bibtex_dict = {'year': str(r['Year'])[:4],
                            'title': r['Title'],
                            'author': author_string}
            # Fuck I don't understand why people try to make bibliographic data relational, it's a headache
            # When there's a perfectly good language designed to hold and express it - bibtex
            # I am sticking it all in a dictionary apart from title, year and authors, and use bibtexparser to convert
            # Now I have to add this and that depending on type. FML. Going to get rid of all empty stuff first
            # See http://www.openoffice.org/bibliographic/bibtex-defs.html for list of relevant bibtex fields
            r = {k: v for k, v in r.items() if pd.notnull(v)}
            # thesis and dissertations, reports

            r['type'] = r['type'].lower()
            if r['type'] == 'article':
                bibtex_dict['ENTRYTYPE'] = 'article'
                if 'Title' in r:
                    bibtex_dict['title'] = r['Title']
                if 'Journal' in r:
                    bibtex_dict['journal'] = r['Journal']
                if 'Editors' in r:
                    bibtex_dict['editor'] = r['Editors']
                if 'Page' in r:
                    bibtex_dict['pages'] = r['Page'].replace('-', '--') # Apparently this is what bibtex wants
                if 'Issue' in r:
                    bibtex_dict['number'] = r['Issue']
                if 'Publisher' in r:
                    bibtex_dict['publisher'] = r['Publisher']
                if 'Pub_locality' in r:
                    bibtex_dict['address'] = r['Pub_locality']
            elif r['type'] == 'book':
                bibtex_dict['ENTRYTYPE'] = 'book'
                if 'Editors' in r:
                    bibtex_dict['editor'] = r['Editors']
                if 'Title' in r:
                    bibtex_dict['title'] = r['Title']
                if 'Pub_locality' in r:
                    bibtex_dict['address'] = r['Pub_locality']
                if 'Publisher' in r:
                    bibtex_dict['publisher'] = r['Publisher']
                if 'Page' in r:
                    bibtex_dict['pages'] = r['Page'].replace('-', '--')

                # We have to do some extra things for book chapters
            elif r['type'] == 'inbook':
                bibtex_dict['ENTRYTYPE'] = 'inbook'
                if 'Editors' in r:
                    bibtex_dict['editor'] = r['Editors']
                if 'Pub_locality' in r:
                    bibtex_dict['address'] = r['Pub_locality']
                if 'Publisher' in r:
                    bibtex_dict['publisher'] = r['Publisher']
                if 'Page' in r:
                    bibtex_dict['pages'] = r['Page'].replace('-', '--')
                if 'Title' in r:
                    bibtex_dict['title'] = r['Title'] # This is the chapter's title. ARGH.
                bibtex_dict['booktitle'] = r['Book_title']
            elif r['type'] == 'techreport' or r['type'] == 'misc':
                if r['type'] == 'techreport':
                    bibtex_dict['ENTRYTYPE'] = 'techreport'
                if r['type'] == 'misc':
                    bibtex_dict['ENTRYTYPE'] = 'misc'
                if 'Publisher' in r:
                    bibtex_dict['institution'] = r['Publisher']
                if 'Title' in r:
                    bibtex_dict['title'] = r['Title']
            else:
                print(r)
                import pdb; pdb.set_trace() # It's some type we haven't thought of yet

            # from bibtexparser.bwriter import BibTexWriter; from bibtexparser.bibdatabase import BibDatabase
            # db = BibDatabase(); db.entries = [bibtex_dict]; writer = BibTexWriter(); writer.write(db)
            # Required for bibtexparser, just putting in a random number for now
            bibtex_dict['ID'] = str(row['Sp_code'])

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

            # Associate with the assessment
            a.references.add(ref)

        # Add Conservation actions
        cons_rows = cons_actions.loc[cons_actions['Sp_code'] == row['Sp_code']]
        for i, c in cons_rows.iterrows():
            # The conservation actions csv contains lots of codes like 3.1.1, we need to look them up

            action_name = c['Item_text'].strip()
            try:
                action, created = redlist_models.Action.objects.get_or_create(name=action_name,
                                                                 action_type=redlist_models.Action.CONSERVATION)
                action_nature = redlist_models.ActionNature.objects.create(assessment=a, action=action)
            except:
                import pdb; pdb.set_trace()

        # Get a list of all contributors/assessors/whatevers for the assessment
        ppl = ppl.loc[ppl['Sp_code'] == row['Sp_code']]
        # people_rows.sort_values(['lastName', 'firstName'], inplace=True)
        for i, p in ppl.iterrows():
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

            if p['surname1'] != '' or pd.notnull(p['surname1']):
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
        ['phylum', row['Phylum']],
        ['class', row['Class']],
        ['order', row['Order_']],
        ['suborder', row['Suborder']],
        ['superfamily', row['Superfamily']],
        ['family', row['Family']],
        ['subfamily', row['Subfamily']],
        ['genus', row['Genus']],
    ]
    for t in taxa_hierarchy:
        if t[1] != '':
            rank, created = models.Rank.objects.get_or_create(name=t[0].title())
            #taxon_name = t[1].strip().capitalize()
            taxon_name = t[1]
            parent, created = models.Taxon.objects.get_or_create(parent=parent, name=taxon_name, rank=rank)

    # Finally add the species to the taxa hierarchy - sometimes this thing only goes go genus level so put it in an if
    if 'Scientific_name' in row:
        rank = models.Rank.objects.get(name='Species')
        species_name = row['Scientific_name'].strip()
        species, created = models.Taxon.objects.get_or_create(parent=parent, name=species_name, rank=rank)
    else:
        species = parent

    if 'Subspecies' in row and row['Subspecies'] != '':
        rank, created = models.Rank.objects.get_or_create(name='Subspecies')
        species_name = parent.name + ' ' + row['Subspecies'].strip()
        species, created = models.Taxon.objects.get_or_create(parent=parent, name=species_name, rank=rank)

    if not created:
        print('species already exists in db')
    else:
        if 'Taxonomic_notes' in row:
            # Add taxon notes if there are any
            taxon_notes = row['Taxonomic_notes']
            #import pdb; pdb.set_trace()
            if taxon_notes is not None and taxon_notes != '':
                species.notes = taxon_notes
                species.save()

        # Create a description and set of references
        if 'Taxonomic_authority' in row:
            imports_views.create_taxon_description(row['Taxonomic_authority'], species, mendeley_session)

    return species, created
