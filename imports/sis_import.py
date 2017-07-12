from taxa import models, helpers
from biblio import models as biblio_models
from people import models as people_models
from redlist import models as redlist_models
from mendeley import Mendeley
from django.http import HttpResponse
import pandas as pd
from psycopg2.extras import NumericRange
from datetime import datetime
import os


def import_phylums():
    """
    Used to create a basic taxa skeleton when you have flushed the db.
    Run python manage.py loaddata taxa_rank.json first to get ranks in
    Not currently used
    """
    life = models.Taxon.objects.create(name='Life', rank_id=9)
    eukaryota = models.Taxon.objects.create(parent=life, name='Eukaryota', rank_id=1)
    plantae = models.Taxon.objects.create(parent=eukaryota, name='Plantae', rank_id=2)
    animalia = models.Taxon.objects.create(parent=eukaryota, name='Animalia', rank_id=2)
    phylums = ['Cnidaria', 'Chordata', 'Porifera', 'Mollusca', 'Arthropoda', 'Annelida', 'Platyhelminthes', 'Myzozoa', 'Nematoda']
    for phylum in phylums:
        p = models.Taxon.objects.create(parent=animalia, name=phylum, rank_id=3)


def import_sis():
    # Start the REST client for mendeley, best to maintain the session throughout the data import
    # Mendeley API doesn't like us instantiating many sessions
    mendeley_id = '3513'
    mendeley_secret = 'gOVvM5RmKseDgcmH'
    mendeley_redirect = 'http://species.sanbi.org'
    mendeley = Mendeley(mendeley_id, client_secret=mendeley_secret, redirect_uri=mendeley_redirect)
    mendeley_session = mendeley.start_client_credentials_flow().authenticate()

    # All of the IUCN SIS data are presented in CSV form
    pwd = os.path.abspath(os.path.dirname(__file__))
    pwd = os.path.join(pwd, '..', 'data-sources')

    # Amphibians
    animal_dirs = ['SIS_Reptiles', os.path.join('SIS_Amphibians', 'draft'), os.path.join('SIS_Amphibians', 'published'),
                   'SIS_Dragonflies', 'SIS_Mammals']
    for animal_dir_name in animal_dirs:
        animal_dir = os.path.join(pwd, animal_dir_name)
        af = pd.read_csv(os.path.join(animal_dir, 'allfields.csv'), encoding='UTF-8') # iso-8859-1
        tx = pd.read_csv(os.path.join(animal_dir, 'taxonomy.csv'), encoding='UTF-8') # iso-8859-1
        cn = pd.read_csv(os.path.join(animal_dir, 'commonnames.csv'), encoding='UTF-8') # UTF-8
        assess = pd.read_csv(os.path.join(animal_dir, 'assessments.csv'), encoding='UTF-8')
        cons_actions = pd.read_csv(os.path.join(animal_dir, 'conservationneeded.csv'), encoding='UTF-8')
        habitats = pd.read_csv(os.path.join(animal_dir, 'habitats.csv'), encoding='UTF-8')
        threats = pd.read_csv(os.path.join(animal_dir, 'threats.csv'), encoding='UTF-8')
        biblio = pd.read_csv(os.path.join(animal_dir, 'references.csv'))
        research = pd.read_csv(os.path.join(animal_dir, 'researchneeded.csv'), encoding='UTF-8')

        # I bet they did this just to annoy all future developers
        ppl = pd.read_csv(os.path.join(animal_dir, 'credits.csv'))
        ppl_old = pd.read_csv(os.path.join(animal_dir, 'credits_old.csv'))

        # Lookups
        research_lookup = pd.read_csv(os.path.join(pwd, 'research_lookup.csv'), encoding='UTF-8')
        threats_lookup = pd.read_csv(os.path.join(pwd, 'threat_lookup.csv'), encoding='UTF-8')
        habitats_lookup = pd.read_csv(os.path.join(pwd, 'habitat_lookup.csv'), encoding='UTF-8')
        cons_actions_lookup = pd.read_csv(os.path.join(pwd, 'cons_actions_lookup.csv'), encoding='UTF-8')

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
            'internal_taxon_id',
            'NoThreats.noThreats',
            'SevereFragmentation.justification'
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

        # Iterate through the taxa table, 1 row represents 1 assessment for a taxon
        for index, taxon_row in tx.iterrows():
        # for index, row in af.iterrows():

            print('----------------------------------------------------------')
            print('row: ' + str(index))
            #if index != 95:
            #    continue

            # Retrieve the taxon info and the assessment we're on
            # taxon_row = t.loc[t['internal_taxon_id'] == row['internal_taxon_id']]
            # taxon_row = taxon_row.iloc[0]
            if 'Exclude' in taxon_row:
                if taxon_row['Exclude'] == 1:
                    print('skipping ' + taxon_row['genus'] + ' ' + taxon_row['species'])
                    continue

            species, species_was_created = create_taxon_from_sis(taxon_row, mendeley_session)

            if 'Exclude' in taxon_row:
                if taxon_row['Exclude'] > 1:
                    print('Excluding species ' + species.name)
                    if 'eptile' in animal_dir_name:
                        a = redlist_models.Assessment(taxon=species, date=datetime.strptime('16/05/2016', '%d/%m/%Y'),
                            redlist_category=taxon_row['status_only'])
                        a.save()
                    continue

            # Replacing this. Should be a one to one mapping between allfields and and taxa anyway
            row = af.loc[af['internal_taxon_id'] == taxon_row['internal_taxon_id']]
            try:
                row = row.iloc[0]
            except IndexError:
                print('Cannot find row in allfields table')
                import pdb; pdb.set_trace()
                continue
            # Remove all row columns which do not contain info
            row = {k: v for k, v in row.items() if pd.notnull(v)}

            # Ignore all species which don't have an assessment. But there's something wrong if we've got one here...
            assess_row = assess.loc[assess['internal_taxon_id'] == row['internal_taxon_id']]
            if len(assess_row) == 0:
                print('No assessment for ' + taxon_row['genus'] + ' ' +  taxon_row['species'])
                import pdb; pdb.set_trace()
                continue

            # The iloc is used because you have to refer to the items via the index e.g. v[0] for row 1, v[1] for row 2, etc
            assess_row = {k: v.iloc[0] for k, v in assess_row.items() if pd.notnull(v.iloc[0])}

            if species_was_created:
                # Add common names and languages for the taxon
                common_names = cn.loc[cn['internal_taxon_id'] == row['internal_taxon_id']]
                for i, c_row in common_names.iterrows():
                    language, created = models.Language.objects.get_or_create(name=c_row['language'].strip())
                    models.CommonName.objects.get_or_create(language=language, name=c_row['name'].strip(),
                                                            taxon=species)

                # All species objects should have a corresponding info object, so let's create one
                info = models.Info(taxon=species)

                # Add any info we can find to the info object, note that a lot of these are missing
                #if 'AvgAnnualFecundity.fecundity' in row:
                #    info.average_fecundity = Decimal(row['AvgAnnualFecundity.fecundity'])
                #if 'BirthSize.size' in row:
                #    try:
                #        info.birth_size = Decimal(row['BirthSize.size'])
                #        info.size_units = models.Info.CM
                #    except:
                #        continue
                #if 'MaxSize.size' in row:
                #    info.max_size = Decimal(row['MaxSize.size'])
                #    info.size_units = models.Info.CM
                #if 'ElevationLower.limit' in row and 'ElevationUpper.limit' in row:
                #    info.altitude_or_depth_range = (int(row['ElevationLower.limit']), int(row['ElevationUpper.limit']))
                if 'Congregatory.value' in row:
                    info.congregatory = [models.Info.CONGREGATORY,
                                         models.Info.DISPERSIVE]  # These all seem to be the same
                if 'EggLaying.layEggs' in row:
                    if row['EggLaying.layEggs'] == 'Yes':
                        info.reproductive_type = [models.Info.EGG_LAYING]
                    elif row['EggLaying.layEggs'] == 'No':
                        info.reproductive_type = [models.Info.LIVE_BIRTH]
                if 'FreeLivingLarvae.hasStage' in row:
                    if row['FreeLivingLarvae.hasStage'] == 'Yes':
                        info.reproductive_type = [models.Info.FREE_LIVING_LARVAE]

                # Get the taxon info stuff from the assessment csv
                info.habitat_narrative = ''
                #if 'System.value' in assess_row:
                #    info.habitat_narrative = '<p class="system">' + assess_row['System.value'] + '</p>'
                if 'HabitatDocumentation.narrative' in assess_row:
                    info.habitat_narrative += assess_row['HabitatDocumentation.narrative']

                info.save()

                # Add habitats, just importing as-is from IUCN, not trying to map to SA habitats - this must be done manually
                habitats_rows = habitats.loc[habitats['internal_taxon_id'] == row['internal_taxon_id']]
                for i, h in habitats_rows.iterrows():
                    lkup = str(h['GeneralHabitats.GeneralHabitatsSubfield.GeneralHabitatsLookup'])
                    if lkup:
                        try:
                            name = habitats_lookup.loc[habitats_lookup['code'] == lkup, 'value']
                            habitat, created = models.Habitat.objects.get_or_create(name=name.iloc[0])
                            info.habitats.add(habitat)
                        except:
                            print('Skipping habitat ' + lkup)
                            pass

                info.save()

            # Create an assessment object and add any necessary info to it
            try:
                assess_date = datetime.strptime(assess_row['RedListAssessmentDate.value'], '%d/%m/%Y') # 01/08/1996
            except:
                assess_date = datetime.strptime('01/12/2016', '%d/%m/%Y')
            a = redlist_models.Assessment(
                taxon=species, date=assess_date
            )
            a.change_rationale = ''
            if 'RedListReasonsForChange.catCritChanges' in assess_row:
                a.change_rationale = assess_row['RedListReasonsForChange.catCritChanges']
            if 'RedListReasonsForChange.changeReasons' in assess_row:
                a.change_rationale += assess_row['RedListReasonsForChange.changeReasons']

            # Distribution stuff
            a.distribution_narrative = ''
            if 'RangeDocumentation.narrative' in assess_row:
                a.distribution_narrative = assess_row['RangeDocumentation.narrative']
            temp = {'Area of occupancy': 'AOO.justification',
                    'Extent of occurrence': 'EOO.justification',
                    'Breeding range': 'AOODetails.breedingRangeJustification',
                    'Non-breeding Range': 'AOODetails.nonbreedingRangeJustification',
                    'Locations': 'LocationsNumber.justification',
                    'Range protection': 'InPlaceLandWaterProtectionInPA.note'}
            #for key, value in temp.items():
            #    if value in row:
            #        a.distribution_narrative += '<h3>' + key + '</h3><div>' + row[value] + '</div>'

            # Distribution/population/habitat decline
            temp = ['AOOContinuingDecline.justification', 'AOOExtremeFluctuation.justification', 'AreaRestricted.justification', 'EOOContinuingDecline.justification', 'EOOExtremeFluctuation.justification', 'HabitatContinuingDecline.justification', 'LocationContinuingDecline.justification', 'LocationExtremeFluctuation.justification', 'SevereFragmentation.justification']
            texts = [row[t] for t in temp if t in row]
            if texts:
                a.distribution_narrative += '<h3>Decline</h3><p>' + '</p><p>'.join(texts) + '</p>'

            if 'ThreatsDocumentation.value' in assess_row:
                a.threats_narrative = assess_row['ThreatsDocumentation.value']
            if 'UseTradeDocumentation.value' in assess_row:
                a.use_trade_narrative = assess_row['UseTradeDocumentation.value']

            p_t = {'Trend': 'PopulationDocumentation.narrative',
                   'Future decline': 'PopulationContinuingDecline.justification',
                   'Fluctuation': 'PopulationExtremeFluctuation.justification'}
            a.population_trend_narrative = ''
            for key, value in p_t.items():
                if value in assess_row:
                    a.population_trend_narrative += '<h3>' + key + '</h3><div>' + assess_row[value] + '</div>'

            #temp = ['ExtinctionProbabilityGenerations3.justification', 'ExtinctionProbabilityGenerations5.justification', 'ExtinctionProbabilityYears100.justification', 'GenerationLength.justification', 'PopulationDeclineGenerations1.justification', 'PopulationDeclineGenerations2.justification', 'PopulationDeclineGenerations3.justification', 'PopulationReductionFuture.justification', 'PopulationReductionPast.justification', 'PopulationReductionPastandFuture.justification', 'SubpopulationContinuingDecline.justification', 'SubpopulationExtremeFluctuation.justification', 'SubpopulationNumber.justification']
            #texts = [row[t] for t in temp if t in row]
            #if texts:
            #    a.population_trend_narrative += '<h3>Decline</h3><p>' + '</p><p>'.join(texts) + '</p>'

            #if 'PopulationTrend.value' in assess_row:
            #    a.population_trend = assess_row['PopulationTrend.value']

            if 'ConservationActionsDocumentation.narrative' in assess_row:
                a.conservation_narrative = assess_row['ConservationActionsDocumentation.narrative']
            if 'AOO.range' in row:
                a_o_upper = row['AOO.range']
                a_o_lower = row['AOO.range']
                if '-' in str(a_o_upper):
                    a_o = a_o_upper.split('-')
                    a_o_lower = a_o[0]
                    a_o_upper = a_o[1]
                a.area_occupancy = NumericRange(int(float(a_o_lower)), int(float(a_o_upper)))
            if 'EOO.range' in row:
                e_o_upper = row['EOO.range']
                e_o_lower = row['EOO.range']
                if '-' in str(e_o_upper):
                    e_o = e_o_upper.split('-')
                    e_o_lower = e_o[0]
                    e_o_upper = e_o[1]
                a.extent_occurrence = NumericRange(int(e_o_lower), int(e_o_upper))
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
                try:
                    authors = helpers.create_authors(r['author'])
                except:
                    import pdb; pdb.set_trace()
                author_string = [x.surname + " " + x.initials for x in authors]
                author_string = ' and '.join(author_string)

                # Sometimes these idiots didn't enter a year, in which case I am throwing the whole reference out
                if pd.isnull(r['year']) or pd.isnull(r['title']):
                    print(r['year'])
                    continue

                # For the year you sometimes have 1981b for example, so just get first 4 chars
                bibtex_dict = {'title': r['title'],
                               'author': author_string}

                try:
                    #if r['year'].strip().lower() != 'in press':
                    int(str(r['year'])[:4])
                    bibtex_dict['year'] = str(r['year'])[:4]
                except ValueError:
                    bibtex_dict['year'] = str(r['year'])

                # I don't understand why people try to make bibliographic data relational, it's a headache
                # When there's a perfectly good language designed to hold and express it - bibtex
                # I am sticking it all in a dictionary apart from title, year and authors, and use bibtexparser to convert
                # Now I have to add this and that depending on type. FML. Going to get rid of all empty stuff first
                # See http://www.openoffice.org/bibliographic/bibtex-defs.html for list of relevant bibtex fields
                r = {k: v for k, v in r.items() if pd.notnull(v)}
                r['type'] = r['type'].lower()

                if r['type'] == 'journal article' or r['type'] == 'rldb' or r['type'] == 'other':
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
                            chapter_authors = helpers.create_authors(r['secondary_author'])
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
                elif r['type'] == 'report':
                    bibtex_dict['ENTRYTYPE'] = 'techreport'
                    if 'publisher' in r:
                        bibtex_dict['institution'] = r['publisher']
                    if 'place_published' in r:
                        bibtex_dict['address'] = r['place_published']
                else:
                    continue
                    # import pdb; pdb.set_trace() # It's some type we haven't thought of yet

                # from bibtexparser.bwriter import BibTexWriter; from bibtexparser.bibdatabase import BibDatabase
                # db = BibDatabase(); db.entries = [bibtex_dict]; writer = BibTexWriter(); writer.write(db)
                # Required for bibtexparser, just putting in a random number for now
                bibtex_dict['ID'] = row['internal_taxon_id']

                # Try and get any preexisting references from the db
                if 'title' in bibtex_dict:
                    ref = biblio_models.Reference.objects.filter(title=bibtex_dict['title']).first()
                    if ref is None:
                        # Create and save the reference object
                        ref = biblio_models.Reference(title=bibtex_dict['title'], bibtex=bibtex_dict)

                        try:
                            ref.year = int(bibtex_dict['year'])
                        except ValueError:
                            pass
                        ref.save()

                        # Assign authors to the reference
                        biblio_models.assign_multiple_authors(authors, ref)

                    # Associate with the assessment
                    a.references.add(ref)

            # Add threats for the assessment by finding all relevant threats and then adding one by one
            threats_rows = threats.loc[threats['internal_taxon_id'] == row['internal_taxon_id']]
            for i, th in threats_rows.iterrows():
                lkup = str(th['Threats.ThreatsSubfield.ThreatsLookup'])
                if lkup:
                    try:
                        name = threats_lookup.loc[threats_lookup['code'] == lkup, 'value']
                        threat, created = redlist_models.Threat.objects.get_or_create(name=name.iloc[0])
                        tn = redlist_models.ThreatNature(assessment=a, threat=threat)
                        if not pd.isnull(th['Threats.ThreatsSubfield.severity']):
                            tn.severity = threat_severity_lookup[th['Threats.ThreatsSubfield.severity']]
                        if not pd.isnull(th['Threats.ThreatsSubfield.timing']):
                            tn.timing = threat_timing_lookup[th['Threats.ThreatsSubfield.timing']]
                        if not pd.isnull(th['Threats.ThreatsSubfield.StressesSubfield.stress']):
                            tn.rationale = th['Threats.ThreatsSubfield.StressesSubfield.stress']
                        tn.save()
                    except:
                        print('Skipping threat ' + lkup)
                        pass

            # Add Conservation actions
            cons_rows = cons_actions.loc[cons_actions['internal_taxon_id'] == row['internal_taxon_id']]
            for i, c in cons_rows.iterrows():
                lkup = str(c['ConservationActions.ConservationActionsSubfield.ConservationActionsLookup'])
                if lkup:
                    try:
                        # The conservation actions csv contains lots of codes like 3.1.1, we need to look them up
                        name = cons_actions_lookup.loc[cons_actions_lookup['code'] == lkup, 'value']
                        action, created = redlist_models.Action.objects.get_or_create(name=name.iloc[0],
                                                                             action_type=redlist_models.Action.CONSERVATION)
                        an = redlist_models.ActionNature(assessment=a, action=action)
                        an.save()
                    except:
                        print('Skipping conservationaction ' + lkup)
                        pass

            # Research needed
            research_rows =  research.loc[research['internal_taxon_id'] == row['internal_taxon_id']]
            for i, r in research_rows.iterrows():
                name = research_lookup.loc[research_lookup['code'] == r['Research.ResearchSubfield.ResearchLookup'], 'value']
                try:
                    action, created = redlist_models.Action.objects.get_or_create(name=name.iloc[0],
                                                                         action_type=redlist_models.Action.RESEARCH)
                    an = redlist_models.ActionNature(assessment=a, action=action)
                    an.save()
                except:
                    print('Skipping researchneeded  ' + r['Research.ResearchSubfield.ResearchLookup'])
                    pass

            # Get a list of all contributors/assessors/whatevers for the assessment
            people_rows = ppl.loc[ppl['internal_taxon_id'] == row['internal_taxon_id']]
            for i, p in people_rows.iterrows():
                if pd.isnull(p['firstName']):
                    person, created = people_models.Person.objects.get_or_create(surname=p['lastName'])
                else:
                    person, created = people_models.Person.objects.get_or_create(first=p['firstName'], surname=p['lastName'])
                if created:
                    person.email = [p['email']]
                    person.initials = p['initials']
                    person.save()
                c = redlist_models.Contribution(person=person, assessment=a, weight=p['Order'],
                                                type=contribution_type_lookup[p['credit_type']])
                c.save()
            people_rows = ppl_old.loc[ppl_old['internal_taxon_id'] == row['internal_taxon_id']]
            for i, p in people_rows.iterrows():
                if p['text'] and not pd.isnull(p['text']) and p['text'].strip() != '':
                    ps = helpers.create_authors(p['text'])
                    for i, person in enumerate(ps):
                        c = redlist_models.Contribution(person=person, assessment=a, weight=i,
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
    species_name = parent.name + ' ' + row['species'].strip().lower()
    species, created = models.Taxon.objects.get_or_create(parent=parent, name=species_name, rank=rank)

    # Subspecies
    if isinstance(row['infra_name'], str):
        print('subspecies')
        # import pdb; pdb.set_trace()
        rank = models.Rank.objects.get(name='Subspecies')
        subspecies_name = species_name + ' ' + row['infra_name'].strip().lower()
        species, created = models.Taxon.objects.get_or_create(parent=species, name=subspecies_name, rank=rank)

    if not created:
        print('species already exists in db')
        import pdb; pdb.set_trace()
    else:
        # Add taxon notes if there are any
        taxon_notes = row['TaxonomicNotes.value']
        if taxon_notes is not None and taxon_notes != '':
            species.notes = taxon_notes
            species.save()

        # Create a description and set of references
        if not pd.isnull(row['taxonomicAuthority']):
            helpers.create_taxon_description(row['taxonomicAuthority'], species, mendeley_session)

    return species, created