from django.shortcuts import render
from rest_framework import generics
from people import models, serializers
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import status
from biblio import models as biblio_models
from biblio import serializers as biblio_serializers
from redlist import serializers as redlist_serializers
from redlist import models as redlist_models
from rest_framework.renderers import TemplateHTMLRenderer, BrowsableAPIRenderer, JSONRenderer


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'people': reverse('people_list', request=request, format=format),
    })


class PeopleList(generics.ListCreateAPIView):
    queryset=models.Person.objects.all()
    serializer_class = serializers.PersonSerializer

    # Overriding super method to use .get_or_create() instead of .save()
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(): # raise_exception=True
            try:
                person = models.Person.objects.get(**serializer.validated_data)
                person = serializers.PersonSerializer(person)
                return Response(person.data, status=status.HTTP_202_ACCEPTED)
            except models.Person.DoesNotExist:
                # Try and get all possible people in the database first
                if serializer.validated_data['initials']:
                    person = models.Person.objects.filter(surname=serializer.validated_data['surname'].strip(),
                                                          initials=serializer.validated_data['initials'].strip(),
                                                          first__startswith=serializer.validated_data['first'][0].strip()).first()
                    if person is None:
                        person = models.Person.objects.filter(surname=serializer.validated_data['surname'].strip(),
                                                              initials=serializer.validated_data['initials'].strip()).first()
                else:
                    person = models.Person.objects.filter(surname=serializer.validated_data['surname'].strip(),
                                                          initials__isnull=True).first()

                # If they cannot be found then create them
                if person is None:
                    self.perform_create(serializer)
                    headers = self.get_success_headers(serializer.data)
                    return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
                else:
                    person = serializers.PersonSerializer(person)
                    return Response(person.data, status=status.HTTP_202_ACCEPTED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@renderer_classes((TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer))
def person(request, slug):
    if request.method == 'GET':
        person = models.Person.objects.get(slug=slug)

        # References
        references = biblio_models.Reference.objects.filter(authors=person, bibtex__isnull=False)
        references = biblio_serializers.ReferenceSerializer(references, many=True)

        # Assessment contributors
        contributions = redlist_models.Contribution.objects.filter(person=person)
        contributions = redlist_serializers.ContributionAssessmentSerializer(contributions, many=True)

        response = {'references': references.data, 'contributions': contributions.data, 'person': str(person)}
        return Response(response, status=status.HTTP_202_ACCEPTED, template_name='website/person.html')
