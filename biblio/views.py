from biblio import models, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from pybib import utils
from rest_framework.decorators import api_view, permission_classes
import re
import requests
import bibtexparser
import pybtex
from io import StringIO
from rest_framework import generics
import pybtex.database.input.bibtex



class RefList(generics.ListCreateAPIView):
    queryset=models.Reference.objects.all()
    serializer_class = serializers.ReferenceWriteSerializer

    # Overriding super method to use .get_or_create() instead of .save()
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(): # raise_exception=True
            instance, created = serializer.get_or_create()
            headers = self.get_success_headers(serializer.data)
            if created:
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            else:
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers)
        else:
            try:
                ref = models.Reference.objects.get(**serializer.data)
                ref = serializers.ReferenceWriteSerializer(ref)
                return Response(ref.data, status=status.HTTP_202_ACCEPTED)
            except models.Reference.DoesNotExist:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



def get_bibtex_from_doi(doi):
    url = "http://dx.doi.org/{}".format(doi)
    headers = {'Accept': 'application/x-bibtex; charset=utf-8'}

    r = requests.get(url, headers=headers)
    r.encoding = "utf-8"

    if r.status_code == 200:
        return r.text.strip()
    elif r.status_code == 404:
        raise ValueError('DOI not found on dx.doi.org')

    return r.status_code


@api_view(['GET'])
def get_bibtex(request, doi):
    # Strip out the forward slash that comes in with URL
    doi = doi.strip('/')

    # First we check to see if the DOI is well-formatted
    doi_regex = r'^10.\d{4,9}/[-._;()/:A-Z0-9]+$'  # See http://blog.crossref.org/2015/08/doi-regular-expressions.html
    match = re.match(doi_regex, doi, flags=re.IGNORECASE)
    if not match:
        return Response('Incorrectly formatted DOI', status=status.HTTP_400_BAD_REQUEST)

    # Then we try and retrieve a bibtex from our database
    try:
        bibtex = models.Reference.objects.get(doi=doi).bibtex
        bibtex = bibtexparser.dumps(bibtex)
    except models.Reference.DoesNotExist:
        # If that's not possible, try and get a bibtex from dx.doi.org
        try:
            bibtex = get_bibtex_from_doi(doi)
        except ValueError:
            bibtex = 'None'

    #parser = pybtex.database.input.bibtex.Parser()
    #import pdb; pdb.set_trace()
    #temp = parser.parse_stream(StringIO(bibtex))

    #p = pybtex.Engine()
    #p.format_from_string(bib_string=bibtex, aux_filename='/static/harvard.bst')
    return Response(bibtex)


class Biblio(APIView):
    """
    List all or create new
    """
    def get(self, request, format=None):
        snippets = models.Reference.objects.all()
        serializer = serializers.ReferenceDOISerializer(snippets, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = serializers.ReferenceDOISerializer(data=request.data)
        if serializer.is_valid():
            import pdb; pdb.set_trace()
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
