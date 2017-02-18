from rest_framework import serializers
from taxa.models import Taxon, Info, CommonName
from rest_framework_recursive.fields import RecursiveField
from biblio.serializers import ReferenceDOISerializer


class ChildrenInfoField(serializers.RelatedField):
    """Used to return count, primary key, name and rank for all child nodes of a taxon, rather than just their pk"""
    def to_representation(self, value):
        child_count = Taxon.objects.get(id=value.id).get_children().count()
        return {'count': child_count, 'id': value.id, 'name': value.name, 'rank': value.rank.id, 'parent_id': value.id }


class ChildCountField(serializers.RelatedField):
    """Used to return count, primary key, name and rank for all child nodes of a taxon, rather than just their pk"""
    def to_representation(self, value):
        child_count = Taxon.objects.get(id=value).get_children().count()
        return child_count


class StringAndKeyField(serializers.RelatedField):
    """Used by jstree to depict rank as well as use rank id in CSS"""
    def to_representation(self, value):
        return {'id': value.id, 'name': value.name}


class TaxonBasicSerializerWithRank(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    rank = StringAndKeyField(read_only=True)
    child_count = ChildCountField(read_only=True, source='id')
    get_latest_assessment = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Taxon
        fields = ('id', 'name', 'parent', 'rank', 'child_count', 'get_top_common_name', 'get_latest_assessment')


class TaxonBasicSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    rank = serializers.PrimaryKeyRelatedField(read_only=True)
    child_count = ChildCountField(read_only=True, source='id')

    class Meta:
        model = Taxon
        fields = ('id', 'name', 'parent', 'rank', 'child_count')


class TaxonChildrenSerializer(serializers.ModelSerializer):
    children = ChildrenInfoField(required=False, many=True, read_only=True)
    rank = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Taxon
        fields = ('id', 'name', 'rank', 'children')


class TaxonLineageSerializer(serializers.ModelSerializer):
    children = ChildrenInfoField(required=False, many=True, read_only=True)
    parent = serializers.StringRelatedField(required=False, read_only=True)
    parent_id = serializers.PrimaryKeyRelatedField(required=False, read_only=True, source='parent')
    rank = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Taxon
        fields = ('id', 'name', 'parent', 'rank', 'children', 'parent_id')


class CommonNameSerializer(serializers.ModelSerializer):
    reference = ReferenceDOISerializer()

    class Meta:
        model = CommonName
        fields = ('name', 'language', 'reference')


class AncestorSerializer(serializers.ModelSerializer):
    rank = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Taxon
        fields = ('id', 'name', 'rank')


class ArrayChoiceFieldSerializer(serializers.RelatedField):
    def to_representation(self, value):
        return [item[1] for item in Info.REPRODUCTIVE_TYPE_CHOICES][0]


class TaxonInfoSerializer(serializers.ModelSerializer):
    habitats = serializers.StringRelatedField(read_only=True, many=True)
    reproductive_type = ArrayChoiceFieldSerializer(read_only=True, many=True)

    class Meta:
        model = Info
        fields = ('morphology',
                  'diagnostics',
                  'trophic',
                  'uses',
                  'movement',
                  'migration_patterns',
                  'congregatory',
                  'reproduction',
                  'reproductive_type',
                  'distribution',
                  'habitat_narrative',
                  'habitats',
                  'altitude_or_depth_range',
                  'maturity_size_female',
                  'maturity_size_male',
                  'max_size',
                  'birth_size',
                  'size_units',
                  'generational_length',
                  'generational_length_narrative',
                  'maturity_age_female',
                  'maturity_age_male',
                  'longevity',
                  'reproductive_age',
                  'gestation_time',
                  'reproductive_periodicity',
                  'average_fecundity',
                  'natural_mortality',
                  'age_units')


class TaxonSerializer(serializers.ModelSerializer):
    children = ChildrenInfoField(required=False, many=True, read_only=True)
    rank = serializers.StringRelatedField(read_only=True)
    get_latest_assessment = serializers.PrimaryKeyRelatedField(read_only=True)
    descriptions = serializers.StringRelatedField(read_only=True, many=True)
    common_names = serializers.StringRelatedField(many=True)
    synonyms = serializers.StringRelatedField(read_only=True, many=True)
    images = serializers.StringRelatedField(many=True)
    info = TaxonInfoSerializer()

    class Meta:
        model = Taxon
        fields = ('id',
                  'name',
                  'rank',
                  'children',
                  'descriptions',
                  'info',
                  'images',
                  'general_distributions',
                  'get_full_name',
                  'common_names',
                  'get_top_common_name',
                  'synonyms',
                  'get_latest_assessment')


class TaxonSuperBasicSerializer(serializers.ModelSerializer):
    children = ChildrenInfoField(required=False, many=True, read_only=True)
    rank = serializers.StringRelatedField(read_only=True)
    common_names = serializers.StringRelatedField(many=True)
    get_latest_assessment = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Taxon
        fields = ('id',
                  'name',
                  'rank',
                  'children',
                  'get_full_name',
                  'common_names',
                  'get_latest_assessment')
