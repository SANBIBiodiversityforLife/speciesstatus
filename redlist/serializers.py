from rest_framework import serializers
from redlist.models import Assessment


class AssessmentSerializer(serializers.ModelSerializer):
    # Fields for overwriting the default serializer classes
    scope = serializers.CharField(source='get_scope_display')
    redlist_category = serializers.CharField(source='get_redlist_category_display')
    population_trend_nature = serializers.CharField(source='get_population_trend_nature_display')
    conservation_actions = serializers.StringRelatedField(read_only=True, many=True)
    references = serializers.StringRelatedField(read_only=True, many=True)

    # threats = models.ManyToManyField(Threat, through='ThreatNature')
    # contributors = models.ManyToManyField(Person, through='Contribution')
    # population_current = IntegerRangeField(null=True, blank=True)
    # subpopulation_number = IntegerRangeField(null=True, blank=True)
    # population_past = IntegerRangeField(null=True, blank=True)
    # population_future = IntegerRangeField(null=True, blank=True)
    # area_occupancy = IntegerRangeField(null=True, blank=True)
    # extent_occurrence = IntegerRangeField(null=True, blank=True)
    # temp_field = HStoreField(null=True, blank=True)

    ##rationale = serializers.CharField()
    ##change_rationale = serializers.CharField()
    ##date = serializers.DateField()
    ##notes = serializers.CharField()
    ##population_trend_narrative = serializers.CharField()
    ##redlist_criteria = serializers.CharField()

    class Meta:
        model = Assessment
        fields = ('id',
                  'taxon',
                  'scope',
                  'rationale',
                  'change_rationale',
                  'date',
                  'notes',
                  'redlist_category',
                  'redlist_criteria',
                  'population_trend_narrative',
                  'population_trend_nature',
                  'conservation_actions',
                  'references')
