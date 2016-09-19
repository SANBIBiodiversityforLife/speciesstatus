from django.shortcuts import render
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from mptt.templatetags.mptt_tags import cache_tree_children
from taxa import models as taxa_models
from taxa import serializers as taxa_serializers
import json
from rest_framework.renderers import JSONRenderer
from mptt.utils import drilldown_tree_for_node

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.http import Http404


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'taxa': reverse('taxon-list', request=request, format=format)
    })



class TaxonDetail(APIView):
    """
    Retrieve a taxon object
    """
    def get_object(self, pk):
        try:
            return taxa_models.Taxon.objects.get(pk=pk)
        except taxa_models.Taxon.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        taxon = self.get_object(pk)
        serializer = taxa_serializers.TaxonSerializer(taxon)
        return Response(serializer.data)




def get_lineage(species_name):
    root = taxa_models.Taxon.objects.filter(name=species_name).first()
    ancestors = root.get_ancestors(include_self=True)
    serializer = taxa_serializers.TaxonSerializer(ancestors, many=True)
    d = serializer.data
    return serializer.data

@api_view()
def index(request):
    template_name = 'website/index.html'
    lineage = get_lineage('Chrysaora fulgida')
    root = taxa_models.Taxon.objects.filter(name='Chrysaora fulgida').first()

    params = {"lineage": JSONRenderer().render(lineage)}
    return Response(params, template_name='website/index.html')
