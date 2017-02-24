from django.shortcuts import render
from rest_framework import generics
from people import models, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import status

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
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            try:
                person = models.Person.objects.get(**serializer.data)
                person = serializers.PersonSerializer(person)
                return Response(person.data, status=status.HTTP_202_ACCEPTED)
            except models.Person.DoesNotExist:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)