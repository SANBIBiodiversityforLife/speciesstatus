from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.utils import formats
from django.contrib.postgres.fields import IntegerRangeField, ArrayField, DateRangeField
from mptt.models import MPTTModel, TreeForeignKey
from biblio.models import Reference
from people.models import Person
from django.utils.text import slugify


class Rank(models.Model):
    """Taxonomic rank, referred to by Taxon model"""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Habitat(models.Model):
    name = models.CharField(max_length=300, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Taxon(MPTTModel):
    """Stores taxonomic information about species/genus/family/order etc all the way up the hierarchy.
    Uses the MPTT and nested set method of hierarchical storage.
    Note that taxa models should never get deleted, they should just be made synonyms of the current name when
    it is added.
    It is assumed that any taxonomic rank (level of hierarchy) can be changed/moved/merged/split.
    Only current names will have info, distribution & common name models.
    """
    # Scientific name
    name = models.CharField(max_length=100)

    # This is used by mptt to build trees, we are just translating directly from GBIF's data
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    # It is important to know when this name was last updated
    updated = models.DateTimeField(auto_now=True)

    # This is the GBIF id for the taxon, it will always be unique
    gbif_id = models.IntegerField(null=True, blank=True)

    # I don't think we can map taxonomic levels directly to depth because some levels are optional, e.g. superfamily
    # Plus they might get changed in time e.g. subspecies might get added. So we are going to steal Specify's tactic:
    # level = models.ForeignKey(TaxonLevelDefinitions)
    rank = models.ForeignKey(Rank, on_delete=models.CASCADE)

    # The references where species are described, for botany they record all of them and for zoology just the first one
    references = models.ManyToManyField(Reference, through='Description')

    # This is populated if it's a taxon is a synonym (merged, split
    current_name = models.ForeignKey('Taxon', on_delete=models.SET_NULL, null=True, blank=True)

    # Used to make friendly URLs
    slug = models.SlugField(max_length=200)

    # If a taxon is merged or split taxonomists often want to record why it happened, this can be entered here
    notes = models.TextField(null=True)

    # Overrides the default save so that we can get a nice URL
    def save(self, *args, **kwargs):
        if not self.id:
            if self.rank == Rank.objects.get(name='Species'):
                self.slug = slugify(str(self.parent) + ' ' + self.name)
            else:
                self.slug = slugify(self.name)

        super(Taxon, self).save(*args, **kwargs)

    # A taxon has synonyms if another taxon is listed as the current name, these are the 'sibling' type nodes
    def synonyms(self):
        if self.current_name:
            # This should really include the current name taxon
            return Taxon.objects.filter(current_name=self.current_name)
        else:
            return Taxon.objects.filter(current_name=self)

    # Handles when a node changes name (name changes but it stays as it is in the tree)
    def name_change(self, new_name):
        # Make a new object which is a copy of the current one
        new_node = self
        new_node.pk = None

        # Refer it to the current object as its current_name
        new_node.current_name = self

        # Save it with the current object's parent
        new_node.insert_at(target=self, position='right', save=True)

        # Change the scientific name
        self.name = new_name
        self.save()
        pass

    # Handles movement of nodes through the tree
    def move_to_new_parent(self, target):
        self.move_to(target, position='first-child')

    # Handles when one node merges with another
    def merge(self, merger):
        # Move all of the children of the current node to the new merger node
        children = self.get_children()
        for child in children:
            child.move_to(merger, position='last-child')

        # Move the common names
        common_names = CommonName.objects.filter(taxon=self)
        for cn in common_names:
            cn.taxon = merger
            try:  # If it's already listed for the merger then ignore the validation error that is triggered
                cn.save()
            except ValidationError:
                pass

        # Delete the info, they should have merged that manually
        info = Info.objects.filter(taxon=self).delete()

        # Merge the distributions, similar to common names we don't want to add anything twice or duplicate polygons
        distributions = GeneralDistribution.objects.filter(taxon=self)
        for dist in distributions:
            dist.taxon = merger
            try:
                dist.save()
            except ValidationError:
                pass

        # Set the current_name for this taxon
        self.current_name = merger
        self.save()

    # Handles when one node splits with another
    def split(self, new_name):
        # Make a new object which is a copy of the current one
        new_node = self
        new_node.pk = None

        # Give it a new name, and insert it as a sibling
        new_node.name = new_name
        new_node.insert_at(target=self, position='right', save=True)

    class Meta:
        verbose_name_plural = 'taxa'
        # Ensure that we don't duplicate taxa
        unique_together = ('name', 'parent', 'rank')

    # This is used when serializing data (geojson, etc) so that we don't get a meaningless number as output
    def natural_key(self):
        return (self.id, self.name)
        # return self.__str__()

    # Required for the MPTT model class
    class MPTTMeta:
        order_insertion_by = ['name']

    # This might need to change back to just self.name
    def __str__(self):
        return self.name

    def get_latest_assessment(self):
        last_assessment = self.assessment_set.last()
        return last_assessment

    # Return a correctly formatted (name + author + date) full name
    def get_full_name(self):
        # Get the number of descriptions and the last description
        descriptions_count = self.descriptions.count()
        last_description = self.descriptions.last()

        # Animals and plants format their full names in different ways when there's more than one description
        plants = Taxon.objects.get(name='Plantae')
        is_plant = self.is_descendant_of(plants)

        # If there's only one result or it's a plant then just return the description
        if descriptions_count == 1 or is_plant:
            return '<em>{}</em>, <span class="species-description">{}</span>'.format(self.name, str(last_description))
        # Otherwise it's an animal and there's more than 1 description
        else:
            return '<em>{}</em>, <span class="species-description">({})</span>'.format(self.name, last_description)

    def get_top_common_name(self):
        top_common_name = CommonName.objects.filter(taxon=self.id).first()
        if top_common_name:
            return top_common_name.name
        else:
            return False


class Description(models.Model):
    # The species that was described
    taxon = models.ForeignKey(Taxon, related_name='descriptions')

    # Where the species was first described, will contain author + year
    reference = models.ForeignKey(Reference, on_delete=models.CASCADE, null=True, blank=True)

    # Describes if the author(s) were the first who described that taxon, or second or third etc.
    # For animals, if author is > 0 the name must get bracketed. Second and third etc authors not important.
    weight = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.reference.get_citation_for_taxon()


class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class CommonName(models.Model):
    """Species may have multiple common names in different languages"""
    name = models.CharField(max_length=200, null=True, blank=True)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    taxon = models.ForeignKey(Taxon, on_delete=models.CASCADE, null=True, blank=True, related_name='common_names')

    # Additionally, store the reference where this common name is first noted
    reference = models.ForeignKey(Reference, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        # Ensure that we don't duplicate common names for a taxon
        unique_together = ('taxon', 'name', 'language')

    def __str__(self):
        if self.reference:
            return '{} ({}, referenced in {})'.format(self.name, self.language, self.reference.get_citation_for_taxon)
        else:
            return '{} ({})'.format(self.name, self.language)


class Info(models.Model):
    taxon = models.OneToOneField(Taxon, related_name='info')

    # Describing the species
    morphology = models.TextField(blank=True)
    diagnostics = models.TextField(blank=True)

    # Trophic strategy
    trophic = models.TextField(blank=True)

    # Random!
    # cites = models.

    # Where the species exists
    habitat_narrative = models.TextField(blank=True)
    habitats = models.ManyToManyField(Habitat, blank=True,
                                      help_text="<strong>Start typing to search through options.</strong> ")

    # Land dwelling plants/animals have altitude, sea dwellers get depth
    altitude_or_depth_range = IntegerRangeField(null=True, blank=True)

    # Size
    maturity_size_female = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    maturity_size_male = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_size = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    birth_size = models.DecimalField(max_digits=5, decimal_places=2,null=True, blank=True)
    MM = "MM"
    CM = "CM"
    M = "M"
    SIZE_UNIT_CHOICES = (
        (CM, 'CM'),
        (MM, 'MM'),
        (M, 'M'),
    )
    size_units = models.CharField(max_length=2, choices=SIZE_UNIT_CHOICES, null=True, blank=True)

    # Life history - Age
    generational_length = IntegerRangeField(null=True, blank=True)
    generational_length_narrative = models.TextField(blank=True)
    maturity_age_female = models.PositiveSmallIntegerField(null=True, blank=True)
    maturity_age_male = models.PositiveSmallIntegerField(null=True, blank=True)
    longevity = models.PositiveSmallIntegerField(null=True, blank=True)
    reproductive_age = models.PositiveSmallIntegerField(null=True, blank=True)
    gestation_time = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2)
    reproductive_periodicity = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2)
    average_fecundity = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    natural_mortality = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    YEARS = 'Y'
    MONTHS = 'M'
    DAYS = 'D'
    HOURS = 'H'
    AGE_UNIT_CHOICES = (
        (YEARS, 'Years'),
        (MONTHS, 'Months'),
        (DAYS, 'Days'),
        (HOURS, 'Hours'),
    )
    age_units = models.CharField(max_length=1, choices=AGE_UNIT_CHOICES, null=True, blank=True)

    # Reproduction
    reproduction = models.TextField(blank=True)
    EGG_LAYING = 'O'
    LIVE_BIRTH = 'V'
    PARTHENOGENESIS = 'P'
    FREE_LIVING_LARVAE = 'F'
    WATER_BREEDING = 'W'
    REPRODUCTIVE_TYPE_CHOICES = (
        (EGG_LAYING, 'Egg laying'),
        (LIVE_BIRTH, 'Live birth'),
        (PARTHENOGENESIS, 'Parthenogenesis'),
        (FREE_LIVING_LARVAE, 'Free living larvae'),
        (WATER_BREEDING, 'Water breeding'),
    )
    reproductive_type = ArrayField(
        models.CharField(choices=REPRODUCTIVE_TYPE_CHOICES, max_length=1, null=True, blank=True), null=True, blank=True
    )

    # Movement behaviour
    movement = models.TextField(blank=True)
    FULL_MIGRANT = 'FM'
    ALTITUDINAL_MIGRANT = 'AM'
    NOT_MIGRANT = 'NM'
    NOMADIC = 'NO'
    UNKNOWN = 'UN'
    MIGRATION_TYPE_CHOICES = (
        (FULL_MIGRANT, 'Full migrant'),
        (ALTITUDINAL_MIGRANT, 'Altitudinal migrant'),
        (NOT_MIGRANT, 'Not a migrant'),
        (NOMADIC, 'Nomadic'),
        (UNKNOWN, 'Unknown'),
    )
    migration_patterns = models.CharField(choices=MIGRATION_TYPE_CHOICES, max_length=2, null=True, blank=True)
    CONGREGATORY = 'CO'
    DISPERSIVE = 'DI'
    CONGREGATORY_YEAR_ROUND = 'CY'
    CONGREGATORY_CHOICES = (
        (CONGREGATORY, 'Congregatroy'),
        (DISPERSIVE, 'Dispersive'),
        (CONGREGATORY_YEAR_ROUND, 'Congregatory year round'),
    )
    congregatory = ArrayField(
        models.CharField(choices=CONGREGATORY_CHOICES, max_length=2, null=True, blank=True), null=True, blank=True
    )


class PointDistribution(models.Model):
    """Point data can be associated with a taxon"""
    taxon = models.ForeignKey(Taxon, related_name='point_distributions')
    point = models.PointField()

    # Record the date range on which the observation was made and who collected it
    date = models.DateField(null=True, blank=True)
    collector = models.ForeignKey(Person)

    # From where we have this data
    origin_code = models.CharField(max_length=100, null=True, blank=True)

    # Uncertainty/precision of the point
    precision_m = models.IntegerField(null=True, blank=True)

    # QDS locus
    qds = models.CharField(max_length=8, null=True, blank=True)


class GeneralDistribution(models.Model):
    """Multiple distribution polygons + corresponding residency status can be associated with a taxon"""
    taxon = models.ForeignKey(Taxon, related_name='general_distributions')

    # Record the date range between which the observations were made
    date = DateRangeField(null=True, blank=True)

    # Specific distribution will come from observations in the wild, but this will give them a rough idea of it
    distribution_polygon = models.PolygonField(null=True, blank=True)

    # For each polygon we want to record if it's endemic or alien etc
    NATIONAL_ENDEMIC = 'END'
    INDIGENOUS = 'IND'
    NATIVE = 'NAT'
    ALIEN = 'ALN'
    INVASIVE = 'INV'
    VAGRANT = 'VAG'
    NEAR_ENDEMIC = 'NEN'
    EXTINCT = 'EXT'
    UNKNOWN = 'UNK'
    RESIDENCY_CHOICES = (
        (NATIONAL_ENDEMIC, 'National endemic'),
        (INDIGENOUS, 'Indigenous'),
        (NATIVE, 'Native'),
        (ALIEN, 'Alien/introduced'),
        (INVASIVE, 'Invasive'),
        (VAGRANT, 'Vagrant'),
        (NEAR_ENDEMIC, 'Near endemic'),
        (EXTINCT, 'Extinct'),
        (UNKNOWN, 'Unknown'),
    )
    residency_status = models.CharField(max_length=3, choices=RESIDENCY_CHOICES, null=True, blank=True)

    COUNTRY = 'C'
    PROVINCE = 'P'
    DISTRICT = 'D'
    OTHER = 'O'
    LEVEL_CHOICES = (
        (COUNTRY, 'Country'),
        (PROVINCE, 'Province'),
        (DISTRICT, 'District'),
        (OTHER, 'Other'),
    )
    level = models.CharField(max_length=1, choices=LEVEL_CHOICES, null=True, blank=True)

    # Description
    description = models.TextField(blank=True)

    # Reference(s?) for the residency status & distribution
    reference = models.ForeignKey(Reference, null=True, blank=True)


class AnimalInfo(models.Model):
    is_migrant = models.BooleanField()


class Image(models.Model):
    taxon = models.ForeignKey(Taxon, related_name='images')
    url = models.CharField(max_length=200)

    def __str__(self):
        return self.url
