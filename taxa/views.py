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
from rest_framework import mixins
from django.shortcuts import get_object_or_404



@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        #'taxa': reverse('lineage', request=request, format=format),
        #'taxon_list': reverse('search_autocomplete', request=request, format=format),
        'taxa': reverse('search_autocomplete', request=request, format=format),
        #'taxon_detail': reverse('detail', request=request, format=format),
    })


class CommonNameDetailFF(APIView):
    """
    List all snippets, or create a new snippet.
    """
    def get(self, request, format=None):
        snippets = models.CommonName.objects.all()
        serializer = serializers.CommonNameSerializer(snippets, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = serializers.CommonNameSerializer(data=request.data)
        if serializer.is_valid():
            import pdb; pdb.set_trace()
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommonNameDetail(mixins.CreateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = models.CommonName.objects.all()
    serializer_class = serializers.CommonNameSerializer

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def get_form(self, request, *args, **kwargs):
        serializer = self.get_serializer()
        return Response({'form': serializer})


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

        #cn = serializers.CommonNameSerializer(), 'cn': cn
        return Response({'taxon': serializer, 'ancestors': ancestors_serializer.data})


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


class LineageView(generics.RetrieveAPIView):
    queryset = models.Taxon.objects.all()
    serializer_class = serializers.TaxonLineageSerializer
    template_name = 'website/tree.html'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        ancestors = instance.get_ancestors(include_self=True)
        serializer = self.get_serializer(ancestors, many=True)
        if TemplateHTMLRenderer in self.renderer_classes:
            params = {"lineage": JSONRenderer().render(serializer.data)}
            return Response(params)
        else:
            return Response(serializer.data)



@api_view(['GET'])
def get_lineage(species_name):
    root = models.Taxon.objects.filter(name=species_name).first()
    ancestors = root.get_ancestors(include_self=True)
    serializer = serializers.TaxonLineageSerializer(ancestors, many=True)
    return Response(serializer.data)
