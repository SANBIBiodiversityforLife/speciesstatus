from redlist import models
from redlist import serializers
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework import generics, pagination
from rest_framework.response import Response


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'assessment': reverse('assessment_list', request=request, format=format),
    })


class TopThreePagination(pagination.PageNumberPagination):
    page_size = 3


class AssessmentList(generics.ListAPIView):
    queryset = models.Assessment.objects.all()
    serializer_class = serializers.AssessmentSerializer
    pagination_class=TopThreePagination


class LastAssessmentDetail(generics.RetrieveAPIView):
    """
    Retrieve the latest assessment for a taxon
    """
    serializer_class = serializers.AssessmentSerializer
    template_name = 'website/assessment.html'
    def get_object(self):
        return models.Assessment.objects.filter(taxon=self.kwargs['taxon_pk']).first()


class AssessmentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Assessment.objects.all()
    serializer_class = serializers.AssessmentSerializer
    template_name = 'website/assessment.html'
