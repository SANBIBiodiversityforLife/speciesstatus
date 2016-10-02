from rest_framework import serializers
from taxa.models import Taxon, Info, CommonName
from rest_framework_recursive.fields import RecursiveField
from biblio.serializers import ReferenceDOISerializer


class ChildrenInfoField(serializers.RelatedField):
    """Used to return count, primary key, name and rank for all child nodes of a taxon, rather than just their pk"""
    def to_representation(self, value):
        child_count = Taxon.objects.get(id=value.id).get_children().count()
        return {'count': child_count, 'id': value.id, 'name': value.name, 'rank': value.rank.id, 'parent_id': value.id }


class TaxonBasicSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    rank = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Taxon
        fields = ('id', 'name', 'parent', 'rank')


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


class TaxonInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Info
        fields = ('morphology',
                  'diagnostics',
                  'movement',
                  'reproduction',
                  'trophic',
                  'uses',
                  'distribution',
                  'habitat',
                  'altitude_or_depth_range')


class TaxonSerializer(serializers.ModelSerializer):
    children = ChildrenInfoField(required=False, many=True, read_only=True)
    rank = serializers.StringRelatedField(read_only=True)
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
                  'synonyms')
