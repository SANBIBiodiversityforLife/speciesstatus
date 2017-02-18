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
import datetime
from decimal import Decimal


def import_spstatus():
    # Start the REST client for mendeley, best to maintain the session throughout the data import
    # Mendeley API doesn't like us instantiating many sessions
    mendeley_id = '3513'
    mendeley_secret = 'gOVvM5RmKseDgcmH'
    mendeley_redirect = 'http://species.sanbi.org'
    mendeley = Mendeley(mendeley_id, client_secret=mendeley_secret, redirect_uri=mendeley_redirect)
    mendeley_session = mendeley.start_client_credentials_flow().authenticate()

    # All of the data were exported from mssql as csv as i wasn't able to connect to mssql via python... sigh
    # Used bcp to do it, which doesn't extract column headings. So i have 1 csv with all col headings
    # Only thing i had to add was column headings "table,column" for the cols csv
    dir = 'C:\\Users\\JohaadienR\\Documents\\Projects\\python-sites\\species\\data-sources\\spstatus\\'
    cols = pd.read_csv(dir + 'cols.csv')

    # Excluded/not using
    # captivefacility country cultivationlevel dataprovider exsitu fragmentation_status history historyfields iucnstatusextended
    # kingdom maps nembastatus nembathreatcategories nembathreats occupancy occurence partsintrade percent propagationtechnique
    # sanbi scientificsynonym scsynonymtemp subpopulation taxclasstemp taxon_dataprovider taxonhabitatinformation
    # taxonnembathreat taxonpartstrade
    percent = pd.read_table(dir + 'percent.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'percent', 'column'])
    change = pd.read_table(dir + 'change.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'change', 'column'])
    class_ = pd.read_table(dir + 'class.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'class', 'column'])
    common_names = pd.read_table(dir + 'commonsynonym.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'commonsynonym', 'column'])
    distribution = pd.read_table(dir + 'distribution.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'distribution', 'column'])
    estimated_pop = pd.read_table(dir + 'estimatedpopulation.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'estimatedpopulation', 'column'])
    family = pd.read_table(dir + 'family.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'family', 'column'])
    habitat = pd.read_table(dir + 'habitat.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'habitat', 'column'])
    iucn = pd.read_table(dir + 'iucnstatus.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'iucnstatus', 'column'])
    language = pd.read_table(dir + 'language.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'language', 'column'])
    uncertainty = pd.read_table(dir + 'levelofuncertainty.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'levelofuncertainty', 'column'])
    order = pd.read_table(dir + 'order.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'order', 'column'])
    phylum = pd.read_table(dir + 'phylum.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'phylum', 'column'])
    population = pd.read_table(dir + 'population.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'population', 'column'])
    province = pd.read_table(dir + 'province.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'province', 'column'])
    qualifier = pd.read_table(dir + 'qualifier.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'qualifier', 'column'])
    decrease = pd.read_table(dir + 'rateofdecrease.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'rateofdecrease', 'column'])
    references = pd.read_table(dir + 'references.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'references', 'column'])
    references = references[pd.notnull(references['taxonid'])] # why??? there are only 2, but why???
    references = references[pd.notnull(references['yearpublished'])] # why??? there are only 2, but why???
    references.loc[:, 'taxonid'] = references.loc[:, 'taxonid'].astype(int)
    region = pd.read_table(dir + 'region.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'region', 'column'])
    reviews = pd.read_table(dir + 'reviews.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'reviews', 'column'])
    contributors = pd.read_table(dir + 'sources.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'reviews', 'column'])
    taxon = pd.read_table(dir + 'taxon.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'taxon', 'column'])
    taxon_habitat = pd.read_table(dir + 'taxonhabitat.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'taxonhabitat', 'column'])
    conservation = pd.read_table(dir + 'taxonmanagement.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'taxonmanagement', 'column'], quoting=csv.QUOTE_NONE, encoding='latin_1')
    taxon_joined = pd.read_table(dir + 'taxonomicclassification.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'taxonomicclassification', 'column'])
    taxon_province = pd.read_table(dir + 'taxonprovince.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'taxonprovince', 'column'])
    taxon_status = pd.read_table(dir + 'taxonstatus.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'taxonstatus', 'column'])
    taxon_threat = pd.read_table(dir + 'taxonthreat.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'taxonthreat', 'column'])
    threat = pd.read_table(dir + 'threat.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'threat', 'column'])
    trade = pd.read_table(dir + 'trade.csv', sep='|', lineterminator='^', names=cols.loc[cols['table'] == 'trade', 'column'])

    # Do some joins so the data is more manageable
    # phylum = chordata
    i_taxon = pd.merge(taxon_joined, family, how='left', left_on='familyid', right_on='identifier', suffixes=('_taxon', '_family'))
    i_taxon = pd.merge(i_taxon, order, how='left', left_on='orderid_taxon', right_on='identifier', suffixes=('_taxon', '_order'))
    i_taxon = pd.merge(i_taxon, class_, how='left', left_on='classid_taxon', right_on='identifier', suffixes=('_taxon', '_class'))
    i_taxon = pd.merge(i_taxon, taxon, how='left', left_on='taxonid', right_on='identifier', suffixes=('_i_taxon', '_orig_taxon'))
    i_taxon.replace(r'^\s+$', pd.np.nan, regex=True, inplace=True)
    i_taxon.replace(r'\s+', ' ', regex=True, inplace=True)
    i_common_names = pd.merge(common_names, language, how='left', left_on='languageid', right_on='identifier', suffixes=('_cn', '_lang'))
    i_taxon_status = pd.merge(taxon_status, iucn, how='left', left_on='iucn_national_status', right_on='identifier')
    i_taxon_status = i_taxon_status.drop_duplicates(subset='taxonid') # No idea why there are duplicates in here, drop them
    i_habitats = pd.merge(taxon_habitat, habitat, left_on='habitatid', right_on='identifier')
    i_distribution = pd.merge(taxon_province, province, how='left', left_on="provinceid", right_on="provid")
    i_population = pd.merge(population, uncertainty, how='left', left_on='population_levelofuncertaintyid', right_on='identifier')
    i_population = pd.merge(i_population, estimated_pop, how='left', left_on='estimatedglobalpopulationid', right_on='identifier')
    i_population = pd.merge(i_population, decrease, how='left', left_on='decreaseinpopulation_percentid', right_on='identifier')
    i_population = pd.merge(i_population, qualifier, how='left', left_on='population_qualifierid', right_on='identifier')
    i_population = pd.merge(i_population, change, how='left', left_on='changeinpopulationid', right_on='identifier')
    i_population = pd.merge(i_population, percent, how='left', left_on='decreaseinpopulation_percentid', right_on='identifier')
    i_threats = pd.merge(taxon_threat, threat, how='left', left_on='threatid', right_on='identifier')

    pop_est_mapping = { '> 10,000': (10001, None), '< 50': (0, 49), '< 250': (50, 249), '< 2,500': (25, 2499), '< 10,000': (2500, 10000), 'Unknown': None }
    # pop_change_mapping = {'Decrease': , 'Increase': , 'Stable': , 'Unknown': }
    percent_mapping = {
        '< 10%': (0, 9),
        '10% or more': (10, 19),
        '20% or more': (20, 29),
        '30% or more': (30, 39),
        '40% or more': (40, 49),
        '50% or more': (50, 59),
        '60% or more': (60, 69),
        '70% or more': (70, 79),
        '80% or more': (80, 89),
        '90% or more': (90, 100),
        'Unknown': None
    }

    redlist_cat_mapping = {
        'Regionally extinct': redlist_models.Assessment.EXTINCT,
        'Critically endangered': redlist_models.Assessment.CRITICALLY_ENDANGERED ,
        'Endangered': redlist_models.Assessment.ENDANGERED,
        'Vulnerable': redlist_models.Assessment.VULNERABLE,
        'Near threatened': redlist_models.Assessment.NEAR_THREATENED,
        'Least concern': redlist_models.Assessment.LEAST_CONCERN,
        'Data deficient': redlist_models.Assessment.DATA_DEFICIENT,
        'Not listed': redlist_models.Assessment.NOT_EVALUATED,
        'Not Set': redlist_models.Assessment.NOT_EVALUATED,
    }

    include_from_assessment = ['singlelocation', 'levelofuncertainty', 'generations_years', 'generationtimefordecline_predicted', 'qualifier']

    # Iterate through the taxon table, 1 row represents 1 assessment for a taxon
    for index, row in i_taxon_status.iterrows():
        print('----------------------------------------------------------')
        print('row: ' + str(index))
        if index < 0:
            continue
        # !import code; code.interact(local=vars())
        # Remove all row columns which do not contain info
        row = {k: v for k, v in row.items() if pd.notnull(v)}

        # Get the corresponding taxon information
        taxon_row = i_taxon.loc[i_taxon['taxonid'] == row['taxonid']]
        if len(taxon_row) == 0:
            continue # I give up....
        taxon_row = {k: v.iloc[0] for k, v in taxon_row.items() if pd.notnull(v.iloc[0])}
        taxon_row['genus'] = taxon_row['genus'].replace(' spp - All species', '')
        taxon_row['genus'] = taxon_row['genus'].replace(' - All species', '')
        species, species_was_created = create_taxon(taxon_row, mendeley_session)

        # If the species was just created add habitat and common names
        if species_was_created:
            if 'niche' in row:
                species.diagnostics = row['niche']
                species.save()

            i_rows = i_common_names.loc[i_common_names['taxonid'] == row['taxonid']]
            for i, c_row in i_rows.iterrows():
                language, created = models.Language.objects.get_or_create(name=c_row['language'].strip())
                try:
                    models.CommonName.objects.get_or_create(language=language, name=c_row['name'].strip(), taxon=species)
                except:
                    import pdb; pdb.set_trace()

            i_rows = i_habitats.loc[i_habitats['taxonid'] == row['taxonid'], 'habitat']
            if len(i_rows):
                info = models.Info(taxon=species)
                info.habitat_narrative = ' / '.join(list(i_rows))
                info.save()

        # Create an assessment object and add any necessary info to it
        if 'iucn_natl_date' not in row or not isinstance(row['iucn_natl_date'], int):
            continue
        assess_date = datetime.date(year=int(row['iucn_natl_date']), month=1, day=1)
        a = redlist_models.Assessment(taxon=species, date=assess_date)
        a.redlist_category = redlist_cat_mapping[row['category']]
        a.redlist_criteria = row['iucn_natl_basis']
        a.rationale = row['notesiucn']

        # Append 'r_others' to rec_notes for the conservation narrative, if there are any r_others rows
        i_rows = conservation.loc[conservation['taxonid'] == row['taxonid']]
        if len(i_rows.loc[pd.notnull(i_rows['r_others'])]) > 0:
            i_rows.loc[pd.notnull(i_rows['r_others']), 'rec_notes'] = i_rows.loc[pd.notnull(i_rows['r_others']), 'rec_notes'].str.strip() + '\r\n' + i_rows.loc[pd.notnull(i_rows['r_others']), 'r_others'].str.strip()
        i_rows = i_rows.loc[pd.notnull(i_rows['rec_notes'])]
        if len(i_rows) > 0:
            a.conservation_narrative = '\r\n'.join(list(i_rows['rec_notes']))

        i_rows = i_population.loc[i_population['taxonid'] == row['taxonid']]
        population = {k: v.iloc[0] for k, v in i_rows.items() if pd.notnull(v.iloc[0])}
        if 'estimatedpopulation' in population:
            a.population_current = pop_est_mapping[population['estimatedpopulation']]
        if 'percentage' in population:
            a.population_future = percent_mapping[population['percentage']]
        if 'fieldstudyinformation' in population:
            a.population_narrative = population['fieldstudyinformation']

        i_rows = i_threats.loc[i_threats['taxonid'] == row['taxonid']]
        # Concatenate threat + note on future threat
        i_rows.loc[pd.notnull(i_rows['notesonfuturethreat']), 'description'] = 'Threat: ' + i_rows.loc[
            pd.notnull(i_rows['notesonfuturethreat']), 'description'] + ' / ' + i_rows.loc[pd.notnull(
            i_rows['notesonfuturethreat']), 'notesonfuturethreat']
        threat_descrips = i_rows.loc[pd.notnull(i_rows['description']), 'description']
        a.threats_narrative = '\r\n'.join(list(threat_descrips))

        hstore_values = {k: v for k, v in row.items() if k in include_from_assessment}
        a.temp_field = hstore_values
        a.save()

        # Yes. References. Anyone who has read the comments for SIS knows how I feel about them.
        ref_rows = references.loc[references['taxonid'].astype(str) == row['taxonid']]
        for i, r in ref_rows.iterrows():
            authors = imports_views.create_authors(r['author'])
            author_string = [x.surname + " " + x.initials for x in authors]
            author_string = ' and '.join(author_string)
            year = str(r['yearpublished'])[:4]

            # The data is SO BAD for these freaking ones I'm going to try find them all on Mendeley
            r = {k: v for k, v in r.items() if pd.notnull(v)}

            # For the year you sometimes have 1981b for example, so just get first 4 chars
            bibtex_dict = {'year': year,
                           'author': author_string}
            if 'title' in r:
                bibtex_dict['title'] = r['title'].strip()
            else:
                bibtex_dict['title'] = '[No title recorded]'

            # They cunningly didn't store reference type, bless their hearts. So i'm putting everything as journal. Bcos.
            bibtex_dict['ENTRYTYPE'] = 'article'
            if 'volume' in r:
                bibtex_dict['number'] = r['volume']
            if 'journal' in r:
                bibtex_dict['journal'] = r['journal']
            if 'publisher' in r:
                bibtex_dict['publisher'] = r['journal']
            if 'pages' in r:
                bibtex_dict['publisher'] = r['pages'].replace('-', '--')
            bibtex_dict['ID'] = row['taxonid']

            # Create and save the reference object
            ref = biblio_models.Reference(year=int(bibtex_dict['year']),
                                          title=bibtex_dict['title'],
                                          bibtex=bibtex_dict)
            ref.save()

            # Assign authors to the reference
            biblio_models.assign_multiple_authors(authors, ref)

            # Associate with the assessment
            a.references.add(ref)


def create_taxon(row, mendeley_session):
    """
    Adds to the taxa hierarchy from spstatus
    :param row:
    :return:
    """
    # Preset the Animalia Kingdom as parent ready for the for loop below
    rank = models.Rank.objects.get(name='Phylum')
    parent = models.Taxon.objects.get(name='Chordata', rank=rank)
    created = False

    # Make a list of the taxa hierarchy from the SIS row in the csv to iterate over
    taxa_hierarchy = [
        ['Class', row['name']],
        ['Order', row['name_order']],
        ['Family', row['name_taxon']],
        ['Genus', row['genus']],
    ]
    for t in taxa_hierarchy:
        rank, created = models.Rank.objects.get_or_create(name=t[0])
        taxon_name = t[1].strip().capitalize()
        parent, created = models.Taxon.objects.get_or_create(parent=parent, name=taxon_name, rank=rank)

    # Finally add the species to the taxa hierarchy - sometimes this thing only goes go genus level so put it in an if
    if 'species' in row:
        rank = models.Rank.objects.get(name='Species')
        species_name = parent.name + ' ' + row['species'].strip()
        species, created = models.Taxon.objects.get_or_create(parent=parent, name=species_name, rank=rank)
    else:
        species = parent

    if 'subspecies' in row:
        rank, created = models.Rank.objects.get_or_create(name='Subspecies')
        species_name = parent.name + ' ' + row['subspecies'].strip()
        species, created = models.Taxon.objects.get_or_create(parent=parent, name=species_name, rank=rank)

    if not created:
        print('species already exists in db')
    else:
        if 'niche' in row:
            # Add taxon notes if there are any
            taxon_notes = row['niche']
            if taxon_notes is not None and taxon_notes != '':
                species.notes = taxon_notes
                species.save()

        # Create a description and set of references
        if 'authority' in row:
            imports_views.create_taxon_description(row['authority'], species, mendeley_session)

    return species, created