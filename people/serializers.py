from rest_framework import serializers
from people.models import Person

class PersonSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='get_type_display')
    person = serializers.StringRelatedField()

    class Meta:
        model = Person
        fields = ('first')