from django.contrib.gis.db import models
from taxa.models import Taxon
from people.models import Person
from biblio.models import Reference
from django.contrib.postgres.fields import IntegerRangeField, HStoreField


class Threat(models.Model):
    name = models.CharField(max_length=300, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Action(models.Model):
    name = models.CharField(max_length=300, unique=True)
    RESEARCH = 'R'
    CONSERVATION = 'C'
    ACTION_TYPE_CHOICES = (
        (RESEARCH, 'Research'),
        (CONSERVATION, 'Conservation')
    )
    action_type = models.CharField(max_length=1, choices=ACTION_TYPE_CHOICES)

    def __str__(self):
        return self.name + '(' + self.action_type + ')'

    class Meta:
        ordering = ['name']


class Assessment(models.Model):
    taxon = models.ForeignKey(Taxon)
    NATIONAL = 'N'
    REGIONAL = 'R'
    GLOBAL = 'G'
    SCOPE_CHOICES = (
        (NATIONAL, 'Regional (South Africa)'),
        (REGIONAL, 'Regional (Other)'),
        (GLOBAL, 'Global')
    )
    scope = models.CharField(max_length=1, choices=SCOPE_CHOICES, default=NATIONAL)
    date = models.DateField()
    threats = models.ManyToManyField(Threat, through='ThreatNature')
    contributors = models.ManyToManyField(Person, through='Contribution')

    EXTINCT = 'EX'
    EXTINCT_IN_WILD = 'EW'
    CRITICALLY_ENDANGERED = 'CR'
    ENDANGERED = 'EN'
    VULNERABLE = 'VU'
    NEAR_THREATENED = 'NT'
    LEAST_CONCERN = 'LC'
    DATA_DEFICIENT = 'DD'
    NOT_EVALUATED = 'NE'
    REDLIST_CATEGORY_CHOICES = (
        (EXTINCT, 'Extinct (EX)'),
        (EXTINCT_IN_WILD, 'Extinct in the Wild (EW)'),
        (CRITICALLY_ENDANGERED, 'Critically Endangered (CR)'),
        (ENDANGERED, 'Endangered (EN)'),
        (VULNERABLE, 'Vulnerable (VU)'),
        (NEAR_THREATENED, 'Near Threatened (NT)'),
        (LEAST_CONCERN, 'Least Concern (LC)'),
        (DATA_DEFICIENT, 'Data Deficient (DD)'),
        (NOT_EVALUATED, 'Not Evaluated (NE)')
    )
    redlist_category = models.CharField(max_length=2, choices=REDLIST_CATEGORY_CHOICES)
    redlist_criteria = models.CharField(max_length=200)

    # Population stuff
    population_current = IntegerRangeField(null=True, blank=True)
    subpopulation_number = IntegerRangeField(null=True, blank=True)
    population_past = IntegerRangeField(null=True, blank=True)
    population_future = IntegerRangeField(null=True, blank=True)
    population_trend = models.CharField(max_length=200, null=True, blank=True)
    UNDERSTOOD = 'U'
    REVERSIBLE = 'R'
    CEASED = 'C'
    POPULATION_TREND_NATURE_CHOICES = (
        (UNDERSTOOD, 'Understood'),
        (REVERSIBLE, 'Reversible'),
        (CEASED, 'Ceased')
    )
    population_trend_nature = models.CharField(max_length=1, choices=POPULATION_TREND_NATURE_CHOICES, null=True, blank=True)

    # Conservation and research actions
    conservation_actions = models.ManyToManyField(Action)

    # Range size - should come from distribution but saved here temporarily
    area_occupancy = IntegerRangeField(null=True, blank=True) # AOO
    extent_occurrence = IntegerRangeField(null=True, blank=True) # EOO

    # Used to store everything that doesn't fit
    temp_field = HStoreField(null=True, blank=True)

    # All the narrative fields which are optional should perhaps go into an hstore?
    # narrative_fields = HStoreField(null=True, blank=True)
    # rationale, changerationale, threats, conservation, research, population, decline/increase, use/trade
    population_trend_narrative = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    rationale = models.TextField(blank=True)
    population_narrative = models.TextField(blank=True)
    change_rationale = models.TextField(blank=True) # Only applicable when the new assessment has different category to previous
    threats_narrative = models.TextField(blank=True)
    conservation_narrative = models.TextField(blank=True)
    research_narrative = models.TextField(blank=True)
    use_trade_narrative = models.TextField(blank=True)
    distribution_narrative = models.TextField(blank=True)

    # I would like users to add references inline in textfields and have some js display a ref list on the page
    # So I hope this field will be temporary
    references = models.ManyToManyField(Reference, blank=True)

    def __str__(self):
        return str(self.taxon) + ' ' + self.redlist_category + ' - ' + str(self.id)

    class Meta:
        ordering = ['date']

class ActionNature(models.Model):
    assessment = models.ForeignKey(Assessment)
    verbose = models.TextField(blank=True)
    UNDERWAY = 'U'
    PROPOSED = 'P'
    COMPLETE = 'C'
    STATUS_CHOICES = (
        (UNDERWAY, 'Underway'),
        (PROPOSED, 'Proposed'),
        (COMPLETE, 'Complete')
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, null=True, blank=True)
    action = models.ForeignKey(Action)


class ThreatNature(models.Model):
    # Unknown is common to all
    UNKNOWN = 'UN'

    EXTREME = 'EX'
    SEVERE = 'SE'
    MODERATE = 'MO'
    SLIGHT = 'SL'
    NONE = 'NO'
    SEVERITY_CHOICES = (
        (EXTREME, 'Extremely severe'),
        (SEVERE, 'Severe'),
        (MODERATE, 'Moderate'),
        (SLIGHT, 'Slight'),
        (NONE, 'No decline'),
        (UNKNOWN, 'Unknown'),
    )
    severity = models.CharField(max_length=2, choices=SEVERITY_CHOICES, default=UNKNOWN, null=True, blank=True)

    PAST = 'PA'
    UNLIKELY_TO_RETURN = 'UR'
    LIKELY_TO_RETURN = 'LR'
    ONGOING = 'ON'
    FUTURE = 'FU'
    POTENTIAL = 'PO'
    TIMING_CHOICES = (
        (PAST, 'Past'),
        (UNLIKELY_TO_RETURN, 'Past, Unlikely to return'),
        (LIKELY_TO_RETURN, 'Past, Likely to return'),
        (ONGOING, 'Ongoing'),
        (FUTURE, 'Future'),
        (POTENTIAL, 'Potential'),
        (UNKNOWN, 'Unknown'),
    )
    timing = models.CharField(max_length=2, choices=TIMING_CHOICES, default=UNKNOWN, null=True, blank=True)

    rationale = models.TextField(blank=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    threat = models.ForeignKey(Threat, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.assessment) + ' - ' + str(self.threat)


class Contribution(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    weight = models.PositiveSmallIntegerField()
    ASSESSOR = 'A'
    REVIEWER = 'R'
    CONTRIBUTOR = 'C'
    FACILITATOR = 'F'
    TYPE_CHOICES = (
        (ASSESSOR, 'Assessor'),
        (REVIEWER, 'Reviewer'),
        (CONTRIBUTOR, 'Contributor'),
        (FACILITATOR, 'Facilitator'),
    )
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)

    def __str__(self):
        return str(self.person)

    class Meta:
        ordering = ['type', 'weight']