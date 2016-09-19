from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.utils import formats
from django.contrib.postgres.fields import IntegerRangeField
from mptt.models import MPTTModel, TreeForeignKey
from biblio.models import Reference
from people.models import Person


class Rank(models.Model):
    """Taxonomic rank, referred to by Taxon model"""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


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

    # The current taxa of a species
    current_name = models.ForeignKey('Taxon', on_delete=models.SET_NULL, null=True, blank=True)

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


class Description(models.Model):
    # The species that was described
    taxon = models.ForeignKey(Taxon)

    # Where the species was first described, will contain author + year
    reference = models.ForeignKey(Reference, on_delete=models.CASCADE, null=True, blank=True)

    # Describes if the author(s) were the first who described that taxon, or second or third etc.
    # For animals, if author is > 0 the name must get bracketed. Second and third etc authors not important.
    weight = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.taxon.name + ' - ' + ', '.join(str(a) for a in self.reference.authors.all())


class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)


class CommonName(models.Model):
    """Species may have multiple common names in different languages"""
    name = models.CharField(max_length=200, null=True, blank=True)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    taxon = models.ForeignKey(Taxon, on_delete=models.CASCADE, null=True, blank=True)

    # Additionally, store the reference where this common name is first noted
    reference = models.ForeignKey(Reference, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        # Ensure that we don't duplicate common names for a taxon
        unique_together = ('taxon', 'name')


class Info(models.Model):
    taxon = models.OneToOneField(Taxon)

    # Describing the species
    morphology = models.TextField(blank=True)
    diagnostics = models.TextField(blank=True)

    movement = models.TextField(blank=True)
    reproduction = models.TextField(blank=True)
    trophic = models.TextField(blank=True)
    uses = models.TextField(blank=True)

    # Where the species exists
    distribution = models.TextField(blank=True)
    habitat = models.TextField(blank=True)

    # Land dwelling plants/animals have altitude, sea dwellers get depth
    altitude_or_depth_range = IntegerRangeField(null=True, blank=True)


class GeneralDistribution(models.Model):
    """Multiple distribution polygons + corresponding residency status can be associated with a taxon"""
    taxon = models.ForeignKey(Taxon)

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
    UNKNOWN = 'UNK'
    RESIDENCY_CHOICES = (
        (NATIONAL_ENDEMIC, 'National endemic'),
        (INDIGENOUS, 'Indigenous'),
        (NATIVE, 'Native'),
        (ALIEN, 'Alien/introduced'),
        (INVASIVE, 'Invasive'),
        (VAGRANT, 'Vagrant'),
        (NEAR_ENDEMIC, 'Near endemic'),
        (UNKNOWN, 'Unknown'),
    )
    residency_status = models.CharField(max_length=3, choices=RESIDENCY_CHOICES)

    # Reference(s?) for the residency status & distribution
    reference = models.ForeignKey(Reference)

    class Meta:
        # Ensure that we don't duplicate distributions for a taxon
        unique_together = ('taxon', 'distribution_polygon')


class AnimalInfo(models.Model):
    is_migrant = models.BooleanField()


class Image(models.Model):
    taxon = models.ForeignKey(Taxon)
    url = models.CharField(max_length=200)
