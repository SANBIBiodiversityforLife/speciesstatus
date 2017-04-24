from biblio import models, serializers
from redlist import models as redlist_models
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import api_view
import re
import requests
import bibtexparser
from taxa import helpers
from rest_framework import generics


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


import bibtexparser
@api_view(['POST'])
def post_bibtex(request):
    assessment = redlist_models.Assessment.objects.get(id=request.data['assessment_id'])
    bibtex = request.data['bibtex']
    db = bibtexparser.loads(bibtex)
    for entry in db.entries:
        bibtex_dict = entry
        ref = models.Reference.objects.filter(bibtex=bibtex_dict).first()
        if ref is None:
            ref = models.Reference(title=bibtex_dict['title'], bibtex=bibtex_dict)
            try:
                ref.year = int(bibtex_dict['year'])
            except ValueError:
                pass
            ref.save()

            # Add the authors
            if 'author' in bibtex_dict:
                authors = helpers.create_authors_from_bibtex_string(bibtex_dict['author'])
                models.assign_multiple_authors(authors, ref)

        assessment.references.add(ref)
    return Response({'Reference added'}, status=status.HTTP_201_CREATED)

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
