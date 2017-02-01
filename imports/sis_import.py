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

def import_sis():
    print('hello')
    return
    dir = 'C:\\Users\\JohaadienR\\Documents\\Projects\\python-sites\\species\\data-sources\\'
    af = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\allfields.csv', encoding='iso-8859-1')
    t = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\taxonomy.csv', encoding='iso-8859-1')
    cn = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\commonnames.csv', encoding='iso-8859-1')
    ppl = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\credits.csv', encoding='iso-8859-1')
    assess = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\assessments.csv', encoding='iso-8859-1')
    cons_actions = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\conservationneeded.csv', encoding='iso-8859-1')
    cons_actions_lookup = pd.read_csv(dir + 'cons_actions_lookup.csv', encoding='iso-8859-1')
    habitats = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\habitats.csv', encoding='iso-8859-1')

    exclude_from_assessment = [
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
        'internal_taxon_id'
    ]

    contribution_type_lookup = {
        'Assessor': redlist_models.Contribution.ASSESSOR,
        'Reviewer': redlist_models.Contribution.REVIEWER,
        'Contributor': redlist_models.Contribution.CONTRIBUTOR,
        'Facilitator': redlist_models.Contribution.FACILITATOR
    }

    # Any duplicates?
    # if len(t.loc[t.duplicated('Redlist_id'), :]) != 0 or len(af.loc[af.duplicated('internal_taxon_id'), :]) != 0:
    #    print('Error, duplicates')
    #    import pdb; pdb.set_trace()

    # Merged
    # df = pd.merge(af, t, left_on='internal_taxon_id', right_on='internal_taxon_id', how='left')

    # Create all taxon objects
    # df.apply(create_taxon_from_sis, axis=1)

    # Iterate through the allfields table, 1 row represents 1 assessment for a taxon
    for index, row in af.iterrows():
        # Retrieve the taxon info for the assessment we're on
        taxon_row = t.loc[t['internal_taxon_id'] == row['internal_taxon_id']]
        import pdb;
        pdb.set_trace()
        species = create_taxon_from_sis(taxon_row)

        # Add common names and languages for the taxon
        common_names = cn.loc[cn['internal_taxon_id'] == t['internal_taxon_id']]
        for cn in common_names.iterrows():
            language = models.Language.objects.get_or_create(name=cn['language'])
            models.CommonName.objects.get_or_create(language=language, name=cn['name'], taxon=species)

        # Remove all row columns which do not contain info
        row = {k: v for k, v in row.items() if pd.notnull(v)}

        # All species objects should have a corresponding info object, so let's create one
        info = models.Info(taxon=species)

        # Add any info we can find to the info object, note that a lot of these are missing
        if 'AvgAnnualFecundity.fecundity' in row:
            info.average_fecundity = row['AvgAnnualFecundity.fecundity']
        if 'BirthSize.size' in row:
            info.birth_size = row['BirthSize.size']
            info.size_units = models.Info.CM
        if 'MaxSize.size' in row:
            info.max_size = row['MaxSize.size']
            info.size_units = models.Info.CM
        if 'Congregatory.value' in row:
            info.congregatory = [models.Info.CONGREGATORY, models.Info.DISPERSIVE]  # These all seem to be the same
        if 'EggLaying.layEggs' in row:
            if row['EggLaying.layEggs'] == 'Yes':
                info.reproductive_type = [models.Info.EGG_LAYING]
            elif row['EggLaying.layEggs'] == 'No':
                info.reproductive_type = [models.Info.LIVE_BIRTH]
        if 'FreeLivingLarvae.hasStage' in row:
            if row['FreeLivingLarvae.hasStage'] == 'Yes':
                info.reproductive_type = [models.Info.FREE_LIVING_LARVAE]
        if 'ElevationLower.limit' in row and 'ElevationUpper.limit' in row:
            info.altitude_or_depth_range = (int(row['ElevationLower.limit']), int(row['ElevationUpper.limit']))

        # Get the taxon info stuff from the assessment csv and save it
        assess_row = assess.loc[assess['internal_taxon_id'] == row['internal_taxon_id']]
        assess_row = {k: v for k, v in assess_row.items() if pd.notnull(v)}
        if 'HabitatDocumentation.narrative' in assess_row:
            info.habitat_narrative = assess_row['HabitatDocumentation.narrative']
        if 'PopulationDocumentation.narrative' in assess_row:
            info.population_trend_narrative = assess_row['PopulationDocumentation.narrative']
        if 'RangeDocumentation.narrative' in assess_row:
            info.distribution = assess_row['RangeDocumentation.narrative']

        info.save()

        # Add habitats

        # Create an assessment object and add any necessary info to it
        a = redlist_models.Assessment(
            taxon=species
        )
        if 'AOO.range' in row:
            a.area_occupancy = NumericRange(row['AOO.range'], row['AOO.range']),
        if 'EOO.range' in row:
            a.extent_occurrence = NumericRange(row['EOO.range'], row['EOO.range']),
        if 'RedListCriteria.manualCategory' in assess_row:
            a.redlist_category = assess_row['RedListCriteria.manualCategory']
        if 'RedListCriteria.manualCriteria' in assess_row:
            a.redlist_criteria = assess_row['RedListCriteria.manualCriteria']
        if 'RedListRationale.value' in assess_row:
            a.rationale = assess_row['RedListRationale.value']

        # Convert all of the other columns data into json and stick it in the temp hstore field
        # There is SO much info and no way to structure it, best if someone goes and pulls it out manually
        # as and when they need it
        hstore_values = {k: v for k, v in row.items() if k not in exclude_from_assessment}
        a.temp_field = hstore_values

        # Save the assessment object now everything has been added to it above
        a.save()

        # Add Conservation actions
        cons_rows = cons_actions.loc[cons_actions['internal_taxon_id'] == row['internal_taxon_id']]
        for i, c in cons_rows.iterrows():
            # The conservation actions csv contains lots of codes like 3.1.1, we need to look them up
            action_name = cons_actions_lookup.loc[cons_actions_lookup['code'] == c['code']]
            action = redlist_models.Action.objects.get_or_create(name=action_name,
                                                                 action_type=redlist_models.Action.CONSERVATION)
            action_nature = redlist_models.ActionNature.objects.create(assessment=a, action=action)

        # Get a list of all contributors/assessors/whatevers for the assessment
        people_rows = ppl.loc[ppl['internal_taxon_id'] == row['internal_taxon_id']]
        # people_rows.sort_values(['lastName', 'firstName'], inplace=True)

        for i, p in people_rows.iterrows():
            person, created = people_models.Person.objects.get_or_create(first=p['firstName'], last=p['lastName'])
            if created:
                person.email = p['email']
                person.initials = p['initials']
                person.save()

            # Add the person as an assessor or contributor to the database
            c = redlist_models.Contribution.objects.create(person=person,
                                                           assessment=a,
                                                           weight=p['Order'],
                                                           type=contribution_type_lookup[p['credit_type']])
            c.save()

    import pdb
    pdb.set_trace()
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
    imports_views.create_taxon_description(row['taxonomicAuthority'], species)

    return species