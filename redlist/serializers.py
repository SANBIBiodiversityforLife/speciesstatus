from rest_framework import serializers
from redlist.models import Assessment, Contribution, Threat, ThreatNature
from taxa.models import Taxon
from bibtexparser.bwriter import BibTexWriter; from bibtexparser.bibdatabase import BibDatabase


class ContributionSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='get_type_display')
    person = serializers.StringRelatedField()

    class Meta:
        model = Contribution
        fields = ('type', 'person', 'weight')


class HstoreSerializer(serializers.CharField):
    def to_representation(self, value):
        return value


class HstoreBibtexField(serializers.RelatedField):
    """Returns bibtex version of json data using bibtexparser"""
    def to_representation(self, value):
        db = BibDatabase()
        writer = BibTexWriter()
        db.entries = [value.bibtex]
        return writer.write(db)


class ThreatNatureSerializer(serializers.HyperlinkedModelSerializer):
    threat = serializers.StringRelatedField(read_only=True)
    severity = serializers.CharField(source='get_severity_display')
    timing = serializers.CharField(source='get_timing_display')

    class Meta:
        model = ThreatNature
        fields = ('severity', 'threat', 'timing')


class AssessmentSerializer(serializers.ModelSerializer):
    # Fields for overwriting the default serializer classes
    scope = serializers.CharField(source='get_scope_display')
    redlist_category_display = serializers.CharField(source='get_redlist_category_display')
    population_trend_nature = serializers.CharField(source='get_population_trend_nature_display')
    taxon = serializers.StringRelatedField(read_only=True)
    taxon_id = serializers.PrimaryKeyRelatedField(read_only=True)
    conservation_actions = serializers.StringRelatedField(read_only=True, many=True)
    references = HstoreBibtexField(read_only=True, many=True)
    date = serializers.DateField(format='%b %Y')
    threats =  ThreatNatureSerializer(source='threatnature_set', many=True)
    contribution_set = ContributionSerializer(read_only=True, many=True)

    # population_current = IntegerRangeField(null=True, blank=True)
    # subpopulation_number = IntegerRangeField(null=True, blank=True)
    # population_past = IntegerRangeField(null=True, blank=True)
    # population_future = IntegerRangeField(null=True, blank=True)
    # area_occupancy = IntegerRangeField(null=True, blank=True)
    # extent_occurrence = IntegerRangeField(null=True, blank=True)
    temp_field = HstoreSerializer()

    class Meta:
        model = Assessment
        fields = ('id',
                  'contribution_set',
                  'taxon',
                  'taxon_id',
                  'scope',
                  'rationale',
                  'change_rationale',
                  'date',
                  'notes',
                  'redlist_category',
                  'redlist_category_display',
                  'redlist_criteria',
                  'population_narrative',
                  'population_trend_narrative',
                  'population_trend_nature',
                  'conservation_actions',
                  'references',
                  'threats',
                  'threats_narrative',
                  'conservation_narrative',
                  'research_narrative',
                  'use_trade_narrative',
                  'distribution_narrative',
                  'temp_field')


class AssessmentWriteSerializer(serializers.ModelSerializer):
    taxon = serializers.PrimaryKeyRelatedField(queryset=Taxon.objects.all())

    class Meta: # notes = inclusion reason
        model = Assessment
        fields = ('id', 'taxon', 'scope', 'date', 'redlist_category', 'redlist_criteria', 'population_trend_narrative',
                  'rationale', 'conservation_narrative', 'distribution_narrative', 'population_narrative', 'notes',
                  'threats_narrative', 'research_narrative', 'change_rationale', 'temp_field')


class ContributionWriteSerializer(serializers.ModelSerializer):
    assessment = serializers.PrimaryKeyRelatedField(queryset=Assessment.objects.all())

    class Meta:
        model = Contribution
        fields = ('assessment', 'person', 'type', 'weight')