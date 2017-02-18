from redlist import models
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.views import APIView
from redlist import serializers
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import filters
from rest_framework import mixins
from mptt.utils import drilldown_tree_for_node

from taxa import serializers as taxon_serializers


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        # 'assessment': reverse('search_autocomplete', request=request, format=format),
        'assessment': reverse('assessment_list', request=request, format=format),
    })


class AssessmentList(generics.ListAPIView):
    queryset = models.Assessment.objects.all()
    serializer_class = serializers.AssessmentSerializer


class AssessmentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Assessment.objects.all()
    serializer_class = serializers.AssessmentSerializer
    template_name = 'website/assessment.html'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        taxon_serializer = taxon_serializers.TaxonSuperBasicSerializer(instance.taxon)

        ancestors = instance.taxon.get_ancestors(include_self=True)
        ancestors_serializer = taxon_serializers.AncestorSerializer(ancestors, many=True)

        contributions = instance.contribution_set.all()
        serialized_contributions = serializers.ContributionSerializer(instance=contributions)
        return Response({'ancestors': ancestors_serializer.data, 'assessment': serializer.data, 'taxon': taxon_serializer, 'contributions': contributions})
