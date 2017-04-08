from taxa import models
from biblio import models as biblio_models
from people import models as people_models
from redlist import models as redlist_models
from mendeley import Mendeley
from django.http import HttpResponse
import pandas as pd
import pymysql
from psycopg2.extras import NumericRange
from imports import views as imports_views
import datetime
from django.contrib.gis.geos import Point


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
    scope_mapping={
        'Regional': redlist_models.Assessment.REGIONAL,
        'Global': redlist_models.Assessment.GLOBAL
    }
    # Iterate through the allfields table, 1 row represents 1 assessment for a taxon
    temp = assess.iloc[:, 162:209]
    temp['Sp_code'] = assess['Sp_code']

    def test(row):
        cats = []
        for index, item in enumerate(row):
            if item != 0 and index != 0:
                cats.append(item)
        return '|'.join(cats)

    p = temp.loc[:, ].replace(1, pd.Series(temp.columns, temp.columns))
    k = p.reindex_axis(['Sp_code'] + list(p.columns[:-1]), axis=1)
    temp_cr = k.apply(test, axis=1)
    assess['criteria'] = temp_cr



    for index, row in assess.iterrows():
        # Retrieve the taxon info for the assessment we're on
        taxon_row = t.loc[t['Sp_code'] == row['Sp_code']]
        taxon_row = {k: v.iloc[0] for k, v in taxon_row.items() if pd.notnull(v.iloc[0])}
        species, created = create_taxon_from_sarca_sabca(taxon_row, mendeley_session)
        if not created:
            print('Taxon created already')
            continue
        # Add common names and languages for the taxon
        if created:
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

            info.habitat_narrative = ''
            if 'sys_Terrestrial' in assess_row:
                if assess_row['sys_Terrestrial'] == 1:
                    info.habitat_narrative = '<p class="system">Terrestrial</p>'
            if 'sys_Habitat' in assess_row:
                info.habitat_narrative = assess_row['sys_Habitat']
            info.save()
            # Add habitats
            a = redlist_models.Assessment(
                taxon=species, date= datetime.date(2014, 1, 1)
            )

            if 'special_Threats_text' in assess_row:
                a.threats_narrative = assess_row['special_Threats_text']

            if 'special_Population_trend' in assess_row:
                a.population_trend = assess_row['special_Population_trend']

            if 'special_Population_blog' in assess_row:
                a.population_trend_narrative = assess_row['special_Population_blog']
            if 'sys_Cons_measures' in assess_row:
                a.conservation_narrative = assess_row['sys_Cons_measures']

            a.distribution_narrative = ''
            if 'Range' in assess_row:
                a.distribution_narrative = assess_row['Range']
            temp = {'Area of occupancy': 'AOO2_notes',
                    'Extent of occurrence': 'EOO2_notes'}
            for key, value in temp.items():
                if value in row:
                    a.distribution_narrative += '<h3>' + key + '</h3><div>' + row[value] + '</div>'

            a.redlist_criteria = assess_row['criteria'].replace('rl_', '')
            if 'Scope' in assess_row:
                a.scope = scope_mapping[assess_row['Scope'].capitalize()]
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
            #hstore_values = {k: v for k, v in row.items() if k not in exclude_from_assessment}
            #a.temp_field = hstore_values

            # Save the assessment object now everything has been added to it above
            #import pdb; pdb.set_trace()
            assessment = a
            try:
                assessment.save()
            except Exception as e:
                print(e)
                import pdb; pdb.set_trace()




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
                assessment = a
                # Associate with the assessment
                assessment.references.add(ref)

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
            ppl_ = ppl.loc[ppl['Sp_code'] == row['Sp_code']]
            # people_rows.sort_values(['lastName', 'firstName'], inplace=True)
            for i, p in ppl_.iterrows():
                if (p['surname'] != '') & (pd.notnull(p['surname'])):
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

            dist = d.loc[d['Sp_code'] == row['Sp_code']]
            for i, occur in dist.iterrows():
                occur = {k: v for k, v in occur.items() if pd.notnull(v)}
                if 'long' in occur and 'lat' in occur:
                    point = models.PointDistribution(taxon=species, point=Point(occur['long'], occur['lat']))
                    if 'year' in occur:
                        day = occur['day'] if 'day' in occur else 1
                        month = occur['month'] if 'month' in occur else 1
                        point.date = datetime.date(int(occur['year']), int(month), int(day))
                    # if 'collector' in occur:
                    #     import pdb; pdb.set_trace()
                    #     person = imports_views.create_authors(occur['collector'])[0]
                    #     point.collector = person
                    if 'locus' in occur:
                        point.qds = str(occur['locus'])[:8]
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
