from rest_framework import serializers
from taxa.models import Taxon
from rest_framework_recursive.fields import RecursiveField


class ChildrenInfoField(serializers.RelatedField):
    """Used to return count, primary key, name and rank for all child nodes of a taxon, rather than just their pk"""
    def to_representation(self, value):
        child_count = Taxon.objects.get(id=value.pk).get_descendant_count()
        return {'count': child_count, 'pk': value.pk, 'name': value.name, 'rank': value.rank.pk}


class TaxonSerializer(serializers.Serializer):
    pk = serializers.IntegerField(read_only=True)
    name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    parent = serializers.StringRelatedField(required=False, read_only=True)
    children = ChildrenInfoField(required=False, many=True, read_only=True)
    rank = serializers.PrimaryKeyRelatedField(read_only=True)

    def create(self, validated_data):
        """"""
        return TaxonSerializer.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """"""
        instance.pk = validated_data.get('pk', instance.pk)
        instance.name = validated_data.get('name', instance.name)
        instance.children = validated_data.get('children', instance.children)
        # instance.parent = validated_data.get('parent', instance.parent)
        instance.save()
        return instance
'''
class TaxonSerializer(serializers.ModelSerializer):
    #parent = serializers.RelatedField(many=True)
    #parent = serializers.RelatedField(many=True)
    parent = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name'
    )
    children = serializers.SlugRelatedField(
        read_only=True,
        many=True,
        slug_field='name'
    )

    class Meta:
        model = Taxon
        fields = ('id', 'name', 'parent', 'children', 'updated', 'rank', 'references')'''


#class TaxonRecursiveSerializer(serializers.Serializer):
#    name = serializers.CharField()
#    children = serializers.ListField(child=RecursiveField())

class TaxonRecursiveSerializer(serializers.ModelSerializer):
    parent = RecursiveField(allow_null=True)

    class Meta:
        model = Taxon
        fields = ('id', 'name', 'parent')
