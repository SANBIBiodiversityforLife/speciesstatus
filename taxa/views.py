from django.shortcuts import render
from taxa import models
from biblio import models as biblio_models
from people import models as people_models
import csv
from suds.client import Client
import requests
from mendeley import Mendeley
import re
from django.db.models import Count
from django.shortcuts import render
from rest_framework.renderers import TemplateHTMLRenderer, BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from mptt.templatetags.mptt_tags import cache_tree_children
from taxa import models as taxa_models
from taxa import serializers
import json
from mptt.utils import drilldown_tree_for_node

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.http import Http404
from rest_framework import status
from rest_framework import generics

from rest_framework import viewsets
from django.contrib.auth.models import User
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework import filters, permissions



@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        #'taxa': reverse('lineage', request=request, format=format),
        #'taxon_list': reverse('search_autocomplete', request=request, format=format),
        'taxa': reverse('search_autocomplete', request=request, format=format),
        #'taxon_detail': reverse('detail', request=request, format=format),
    })


class CommonNameDetail(generics.CreateAPIView):
    queryset = models.CommonName.objects.all()
    serializer_class = serializers.CommonNameSerializer


class TaxonDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Taxon.objects.all()
    serializer_class = serializers.TaxonSerializer
    template_name = 'website/taxon.html'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        ancestors = instance.get_ancestors(include_self=True)
        #ancestor_serializer = serializers.AncestorSerializer(ancestors, many=True)
        #return Response({'data': serializer.data, 'ancestors': ancestor_serializer.tree_path()})
        ancestors_serializer = serializers.AncestorSerializer(ancestors, many=True)
        common_name = models.CommonName.objects.get(id=2)
        cn = serializers.CommonNameSerializer(common_name)
        return Response({'taxon': serializer.data, 'ancestors': ancestors_serializer.data, 'cn': cn})


class TaxonListView(generics.ListAPIView):
    queryset = models.Taxon.objects.all()
    serializer_class = serializers.TaxonSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',
                     'info__morphology',
                     'info__diagnostics',
                     'info__movement',
                     'info__reproduction',
                     'info__trophic',
                     'info__uses',
                     'info__distribution',
                     'info__habitat',
                     'common_names__name')


@api_view(['GET'])
def get_lineage(species_name):
    root = models.Taxon.objects.filter(name=species_name).first()
    ancestors = root.get_ancestors(include_self=True)
    serializer = serializers.TaxonLineageSerializer(ancestors, many=True)
    return Response(serializer.data)
