from rest_framework import serializers
from biblio.models import Reference


class ReferenceDOISerializer(serializers.ModelSerializer):
    class Meta:
        model = Reference
        fields = ('doi', 'bibtex')


class ReferenceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reference
        fields = ('title', 'year', 'bibtex')