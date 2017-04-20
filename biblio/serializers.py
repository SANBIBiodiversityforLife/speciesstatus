from rest_framework import serializers
from biblio.models import Reference
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase


class ReferenceDOISerializer(serializers.ModelSerializer):
    class Meta:
        model = Reference
        fields = ('doi', 'bibtex')


class ReferenceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reference
        fields = ('title', 'year', 'bibtex')


class HstoreBibtexField(serializers.CharField):
    """Returns bibtex version of json data using bibtexparser"""

    def to_representation(self, value):
        db = BibDatabase()
        writer = BibTexWriter()
        db.entries = [value]
        return writer.write(db)


class ReferenceSerializer(serializers.ModelSerializer):
    bibtex = HstoreBibtexField()

    class Meta:
        model = Reference
        fields = ('bibtex',)
