from django.contrib.gis.db import models
from taxa.models import Taxon
from people.models import Person
from django.contrib.postgres.fields import IntegerRangeField, ArrayField, DateRangeField, HStoreField


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
    rationale = models.TextField()
    change_rationale = models.TextField() # Only applicable when the new assessment has different category to previous
    date = models.DateField()
    notes = models.TextField()
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
        (EXTINCT, 'EX'),
        (EXTINCT_IN_WILD, 'EW'),
        (CRITICALLY_ENDANGERED, 'CR'),
        (ENDANGERED, 'EN'),
        (VULNERABLE, 'VU'),
        (NEAR_THREATENED, 'NT'),
        (LEAST_CONCERN, 'LC'),
        (DATA_DEFICIENT, 'DD'),
        (NOT_EVALUATED, 'NE')
    )
    redlist_category = models.CharField(max_length=2, choices=REDLIST_CATEGORY_CHOICES)
    redlist_criteria = models.CharField(max_length=100)

    # Population stuff
    population_current = IntegerRangeField(null=True, blank=True)
    subpopulation_number = IntegerRangeField(null=True, blank=True)
    population_past = IntegerRangeField(null=True, blank=True)
    population_future = IntegerRangeField(null=True, blank=True)
    UNDERSTOOD = 'U'
    REVERSIBLE = 'R'
    CEASED = 'C'
    POPULATION_TREND_NATURE_CHOICES = (
        (UNDERSTOOD, 'Understood'),
        (REVERSIBLE, 'Reversible'),
        (CEASED, 'Ceased')
    )
    population_trend_nature = models.CharField(max_length=1, choices=POPULATION_TREND_NATURE_CHOICES, null=True, blank=True)
    population_trend_narrative = models.TextField(blank=True)

    # Conservation and research actions
    conservation_actions = models.ManyToManyField(Action)

    # Range size - should come from distribution but saved here temporarily
    area_occupancy = IntegerRangeField(null=True, blank=True) # AOO
    extent_occurrence = IntegerRangeField(null=True, blank=True) # EOO
    temp_field = HStoreField(null=True, blank=True)


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
    EXTREME = 'EX'
    SEVERE = 'SE'
    MODERATE = 'MO'
    SLIGHT = 'SL'
    NONE = 'NO'
    UNKNOWN = 'UN'
    IMPACT_CHOICES = (
        (EXTREME, 'Extreme'),
        (SEVERE, 'Severe'),
        (MODERATE, 'Moderate'),
        (SLIGHT, 'Slight'),
        (NONE, 'None'),
        (UNKNOWN, 'Unknown'),
    )
    impact = models.CharField(max_length=2, choices=IMPACT_CHOICES, default=UNKNOWN)

    PAST = 'PA'
    UNLIKELY_TO_RETURN = 'UR'
    LIKELY_TO_RETURN = 'LR'
    ONGOING = 'ON'
    FUTURE = 'FU'
    POTENTIAL = 'PO'
    UNKNOWN = 'UN'
    TIMING_CHOICES = (
        (PAST, 'Past'),
        (UNLIKELY_TO_RETURN, 'Unlikely to return'),
        (LIKELY_TO_RETURN, 'Likely to return'),
        (ONGOING, 'Ongoing'),
        (FUTURE, 'Future'),
        (POTENTIAL, 'Potential'),
        (UNKNOWN, 'Unknown'),
    )
    timing = models.CharField(max_length=2, choices=TIMING_CHOICES, default=UNKNOWN)

    rationale = models.TextField(blank=True)

    # Foreign keys
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    threat = models.ForeignKey(Threat, on_delete=models.CASCADE)


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
