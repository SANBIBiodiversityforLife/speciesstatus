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
from datetime import datetime
from decimal import Decimal


def import_sis():
    # Start the REST client for mendeley, best to maintain the session throughout the data import
    # Mendeley API doesn't like us instantiating many sessions
    mendeley_id = '3513'
    mendeley_secret = 'gOVvM5RmKseDgcmH'
    mendeley_redirect = 'http://species.sanbi.org'
    mendeley = Mendeley(mendeley_id, client_secret=mendeley_secret, redirect_uri=mendeley_redirect)
    mendeley_session = mendeley.start_client_credentials_flow().authenticate()

    # All of the IUCN SIS data are presented in CSV form
    dir = 'C:\\Users\\JohaadienR\\Documents\\Projects\\python-sites\\species\\data-sources\\'
    af = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\allfields.csv', encoding='iso-8859-1')
    t = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\taxonomy.csv', encoding='iso-8859-1')
    cn = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\commonnames.csv', encoding='iso-8859-1')
    ppl = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\credits.csv', encoding='iso-8859-1')
    assess = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\assessments.csv', encoding='iso-8859-1')
    cons_actions = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\conservationneeded.csv', encoding='iso-8859-1')
    cons_actions_lookup = pd.read_csv(dir + 'cons_actions_lookup.csv', encoding='iso-8859-1')
    habitats = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\habitats.csv', encoding='iso-8859-1')
    habitats_lookup = pd.read_csv(dir + 'habitat_lookup.csv', encoding='iso-8859-1')
    threats = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\threats.csv', encoding='iso-8859-1')
    threats_lookup = pd.read_csv(dir + 'threat_lookup.csv', encoding='iso-8859-1')
    biblio = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\references.csv', encoding='iso-8859-1')
    research = pd.read_csv(dir + 'Amphibians_SIS\\Amphibians\\researchneeded.csv', encoding='iso-8859-1')
    research_lookup = pd.read_csv(dir + 'research_lookup.csv', encoding='iso-8859-1')

    # These lists we use below as we iterate over all the assessments
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
    threat_timing_lookup = {
        'Ongoing': redlist_models.ThreatNature.PAST,
        'Future': redlist_models.ThreatNature.FUTURE,
        'Unknown': redlist_models.ThreatNature.UNKNOWN,
        'Past, Likely to Return': redlist_models.ThreatNature.LIKELY_TO_RETURN,
        'Past, Unlikely to Return': redlist_models.ThreatNature.UNLIKELY_TO_RETURN
    }
    threat_severity_lookup = {
        'Very Rapid Declines': redlist_models.ThreatNature.EXTREME,
        'Rapid Declines': redlist_models.ThreatNature.SEVERE,
        'Slow, Significant Declines': redlist_models.ThreatNature.SEVERE,
        'Causing/Could cause fluctuations': redlist_models.ThreatNature.MODERATE,
        'Negligible declines': redlist_models.ThreatNature.SLIGHT,
        'No decline': redlist_models.ThreatNature.NONE,
        'Unknown': redlist_models.ThreatNature.UNKNOWN
    }

    # Iterate through the allfields table, 1 row represents 1 assessment for a taxon
    for index, row in af.iterrows():
        print('----------------------------------------------------------')
        print('row: ' + str(index))

        # Retrieve the taxon info for the assessment we're on
        taxon_row = t.loc[t['internal_taxon_id'] == row['internal_taxon_id']]
        taxon_row = taxon_row.iloc[0]
        species = create_taxon_from_sis(taxon_row, mendeley_session)

        # Add common names and languages for the taxon
        common_names = cn.loc[cn['internal_taxon_id'] == row['internal_taxon_id']]
        for i, c_row in common_names.iterrows():
            language, created = models.Language.objects.get_or_create(name=c_row['language'].strip())
            models.CommonName.objects.get_or_create(language=language, name=c_row['name'].strip(), taxon=species)

        # Remove all row columns which do not contain info
        row = {k: v for k, v in row.items() if pd.notnull(v)}

        # All species objects should have a corresponding info object, so let's create one
        info = models.Info(taxon=species)

        # Add any info we can find to the info object, note that a lot of these are missing
        if 'AvgAnnualFecundity.fecundity' in row:
            info.average_fecundity = Decimal(row['AvgAnnualFecundity.fecundity'])
        if 'BirthSize.size' in row:
            info.birth_size = Decimal(row['BirthSize.size'])
            info.size_units = models.Info.CM
        if 'MaxSize.size' in row:
            info.max_size = Decimal(row['MaxSize.size'])
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

        # Get the taxon info stuff from the assessment csv and remove all empty values
        # The iloc is used because you have to refer to the items via the index e.g. v[0] for row 1, v[1] for row 2, etc
        assess_row = assess.loc[assess['internal_taxon_id'] == row['internal_taxon_id']]
        assess_row = {k: v.iloc[0] for k, v in assess_row.items() if pd.notnull(v.iloc[0])}

        if 'HabitatDocumentation.narrative' in assess_row:
            info.habitat_narrative = assess_row['HabitatDocumentation.narrative']
        if 'PopulationDocumentation.narrative' in assess_row:
            info.population_trend_narrative = assess_row['PopulationDocumentation.narrative']
        if 'RangeDocumentation.narrative' in assess_row:
            info.distribution = assess_row['RangeDocumentation.narrative']

        info.save()

        # Add habitats, just importing as-is from IUCN, not trying to map to SA habitats - this must be done manually
        habitats_rows = habitats.loc[habitats['internal_taxon_id'] == row['internal_taxon_id']]
        for i, h in habitats_rows.iterrows():
            name = habitats_lookup.loc[habitats_lookup['code'] == h['GeneralHabitats.GeneralHabitatsSubfield.GeneralHabitatsLookup'], 'value']
            habitat, created = models.Habitat.objects.get_or_create(name=name)
            info.habitats.add(habitat)

        # Create an assessment object and add any necessary info to it
        assess_date = datetime.strptime(assess_row['RedListAssessmentDate.value'], '%d/%m/%Y') # 01/08/1996
        a = redlist_models.Assessment(
            taxon=species, date=assess_date
        )
        if 'AOO.range' in row:
            a.area_occupancy = NumericRange(int(row['AOO.range']), int(row['AOO.range']))
        if 'EOO.range' in row:
            a.extent_occurrence = NumericRange(int(row['EOO.range']), int(row['EOO.range']))
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
        try:
            a.save()
        except:
            import pdb; pdb.set_trace()

        # References for the redlist assessment - nightmarish
        ref_rows = biblio.loc[biblio['internal_taxon_id'] == row['internal_taxon_id']]
        for i, r in ref_rows.iterrows():
            authors = imports_views.create_authors(r['author'])
            author_string = [x.surname + " " + x.initials for x in authors]
            author_string = ' and '.join(author_string)

            # Sometimes these idiots didn't enter a year, in which case I am throwing the whole reference out
            if pd.isnull(r['year']):
                print(r['year'])
                continue

            # For the year you sometimes have 1981b for example, so just get first 4 chars
            bibtex_dict = {'year': str(r['year'])[:4],
                           'title': r['title'],
                           'author': author_string}

            # Fuck I don't understand why people try to make bibliographic data relational, it's a headache
            # When there's a perfectly good language designed to hold and express it - bibtex
            # I am sticking it all in a dictionary apart from title, year and authors, and use bibtexparser to convert
            # Now I have to add this and that depending on type. FML. Going to get rid of all empty stuff first
            # See http://www.openoffice.org/bibliographic/bibtex-defs.html for list of relevant bibtex fields
            r = {k: v for k, v in r.items() if pd.notnull(v)}
            r['type'] = r['type'].lower()
            if r['type'] == 'journal article':
                bibtex_dict['ENTRYTYPE'] = 'article'
                if 'volume' in r:
                    bibtex_dict['volume'] = r['volume']
                if 'secondary_title' in r:
                    bibtex_dict['journal'] = r['secondary_title']
                if 'pages' in r:
                    bibtex_dict['pages'] = r['pages'].replace('-', '--') # Apparently this is what bibtex wants
                if 'number' in r:
                    bibtex_dict['number'] = r['number']
            elif r['type'] == 'book' or r['type'] == 'book section' or r['type'] == 'edited book':
                bibtex_dict['ENTRYTYPE'] = 'book'
                if 'place_published' in r:
                    bibtex_dict['address'] = r['place_published']
                if 'publisher' in r:
                    bibtex_dict['publisher'] = r['publisher']

                # We have to do some extra things for book chapters
                if r['type'] == 'book section':
                    bibtex_dict['ENTRYTYPE'] = 'inbook'
                    if 'pages' in r:
                        bibtex_dict['pages'] = r['pages'].replace('-', '--')
                    if 'secondary_title' in r:
                        bibtex_dict['title'] = r['secondary_title'] # This is the chapter's title. ARGH.
                    bibtex_dict['booktitle'] = r['title']
                    if 'secondary_author' in r:
                        chapter_authors = imports_views.create_authors(r['secondary_author'])
                        chapter_author_string = ' and '.join([x.surname + " " + x.initials for x in chapter_authors])
                        authors = chapter_authors
                        bibtex_dict['editor'] = author_string
                        bibtex_dict['author'] = chapter_author_string
            elif r['type'] == 'thesis':
                bibtex_dict['ENTRYTYPE'] = 'phdthesis'
                if 'publisher' in r:
                    bibtex_dict['school'] = r['publisher']
            elif r['type'] == 'conference proceedings' or r['type'] == 'conference paper':
                bibtex_dict['ENTRYTYPE'] = 'proceedings'
                bibtex_dict['editor'] = author_string
                del bibtex_dict['author']
                if 'secondary_title' in r:
                    bibtex_dict['series'] = r['secondary_title']
                if 'publisher' in r:
                    bibtex_dict['publisher'] = r['publisher']
                if 'place_published' in r:
                    bibtex_dict['address'] = r['place_published']
            elif r['type'] == 'electronic source':
                bibtex_dict['ENTRYTYPE'] = 'electronic'
                if 'url' in r:
                    bibtex_dict['address'] = r['url']
                if 'publisher' in r:
                    bibtex_dict['publisher'] = r['publisher']
            else:
                print(r)
                import pdb; pdb.set_trace() # It's some type we haven't thought of yet

            # from bibtexparser.bwriter import BibTexWriter; from bibtexparser.bibdatabase import BibDatabase
            # db = BibDatabase(); db.entries = [bibtex_dict]; writer = BibTexWriter(); writer.write(db)
            # Required for bibtexparser, just putting in a random number for now
            bibtex_dict['ID'] = row['internal_taxon_id']

            # Create and save the reference object
            ref = biblio_models.Reference(year=int(bibtex_dict['year']),
                                          title=bibtex_dict['title'],
                                          bibtex=bibtex_dict)
            ref.save()

            # Assign authors to the reference
            biblio_models.assign_multiple_authors(authors, ref)

            # Associate with the assessment
            a.references.add(ref)

        # Add threats for the assessment by finding all relevant threats and then adding one by one
        threats_rows = threats.loc[threats['internal_taxon_id'] == row['internal_taxon_id']]
        for i, th in threats_rows.iterrows():
            name = threats_lookup.loc[threats_lookup['code'] == th['Threats.ThreatsSubfield.ThreatsLookup'], 'value']
            threat, created = redlist_models.Threat.objects.get_or_create(name=name)
            tn = redlist_models.ThreatNature(assessment=a, threat=threat)
            if not pd.isnull(th['Threats.ThreatsSubfield.severity']):
                tn.severity = threat_severity_lookup[th['Threats.ThreatsSubfield.severity']]
            if not pd.isnull(th['Threats.ThreatsSubfield.timing']):
                tn.timing = threat_timing_lookup[th['Threats.ThreatsSubfield.timing']]
            if not pd.isnull(th['Threats.ThreatsSubfield.StressesSubfield.stress']):
                tn.rationale = th['Threats.ThreatsSubfield.StressesSubfield.stress']
            tn.save()

        # Add Conservation actions
        cons_rows = cons_actions.loc[cons_actions['internal_taxon_id'] == row['internal_taxon_id']]
        for i, c in cons_rows.iterrows():
            # The conservation actions csv contains lots of codes like 3.1.1, we need to look them up
            action_name = cons_actions_lookup.loc[cons_actions_lookup['code'] == c['ConservationActions.ConservationActionsSubfield.ConservationActionsLookup'], 'value']
            action, created = redlist_models.Action.objects.get_or_create(name=action_name,
                                                                 action_type=redlist_models.Action.CONSERVATION)
            an = redlist_models.ActionNature(assessment=a, action=action)
            an.save()

        # Research needed
        research_rows =  research.loc[research['internal_taxon_id'] == row['internal_taxon_id']]
        for i, r in research_rows.iterrows():
            research_name = research_lookup.loc[research_lookup['code'] == r['Research.ResearchSubfield.ResearchLookup'], 'value']
            action, created = redlist_models.Action.objects.get_or_create(name=research_name,
                                                                 action_type=redlist_models.Action.RESEARCH)
            an = redlist_models.ActionNature(assessment=a, action=action)
            an.save()

        # Get a list of all contributors/assessors/whatevers for the assessment
        people_rows = ppl.loc[ppl['internal_taxon_id'] == row['internal_taxon_id']]
        for i, p in people_rows.iterrows():
            person, created = people_models.Person.objects.get_or_create(first=p['firstName'], surname=p['lastName'])
            if created:
                person.email = [p['email']]
                person.initials = p['initials']
                person.save()
            c = redlist_models.Contribution(person=person, assessment=a, weight=p['Order'],
                                            type=contribution_type_lookup[p['credit_type']])
            c.save()
    import pdb; pdb.set_trace()
    print('done')
    return HttpResponse('<html><body><p>Done</p></body></html>')


def create_taxon_from_sis(row, mendeley_session):
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
        ['Phylum', row['phylum']],
        ['Class', row['classname']],
        ['Order', row['ordername']],
        ['Family', row['family']],
        ['Genus', row['genus']],
    ]
    for t in taxa_hierarchy:
        rank, created = models.Rank.objects.get_or_create(name=t[0])
        taxon_name = t[1].strip().capitalize()
        parent, created = models.Taxon.objects.get_or_create(parent=parent, name=taxon_name, rank=rank)

    # Finally add the species to the taxa hierarchy
    rank = models.Rank.objects.get(name='Species')
    species_name = parent.name + ' ' + row['species'].strip()
    species, created = models.Taxon.objects.get_or_create(parent=parent, name=species_name, rank=rank)

    # Add taxon notes if there are any
    taxon_notes = row['TaxonomicNotes.value']
    if taxon_notes is not None and taxon_notes != '':
        species.notes = taxon_notes
        species.save()

    # Create a description and set of references
    imports_views.create_taxon_description(row['taxonomicAuthority'], species, mendeley_session)

    return species