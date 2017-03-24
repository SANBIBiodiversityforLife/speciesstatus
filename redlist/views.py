from redlist import models
from taxa import models as taxa_models
from redlist import serializers
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework import generics, pagination
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'assessment list top 3': reverse('assessment_list', request=request, format=format),
        'assessment list or write': reverse('assessment_write', request=request, format=format),
        'contribution list or write': reverse('contribution_write', request=request, format=format),
        'statistics': reverse('redlist_statistics', request=request, format=format),
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


class AssessmentWrite(generics.ListCreateAPIView):
    queryset = models.Assessment.objects.all()
    serializer_class = serializers.AssessmentWriteSerializer


class ContributionWrite(generics.ListCreateAPIView):
    queryset = models.Contribution.objects.all()
    serializer_class = serializers.ContributionWriteSerializer


@api_view(['GET'])
def redlist_statistics_old(request):
    """
    Returns interesting stats about the db
    """
    if request.method == 'GET':
        class_rank = taxa_models.Rank.objects.get(name='Class')
        class_nodes = taxa_models.Taxon.objects.filter(rank=class_rank)
        statuses = models.Assessment.REDLIST_CATEGORY_CHOICES
        data = []
        node_names = [t.name for t in class_nodes]
        for stat_id, stat_value in statuses:
            node_statuses = {}
            for node in class_nodes:
                count = node.get_descendants().filter(assessment__redlist_category=stat_id).count()
                node_statuses[node.name] = count
            data.append({stat_value: node_statuses})
        import pprint
        pprint.pprint(data)
        resp = {'statistics': data, 'orders': node_names, 'statuses': [s[1] for s in statuses]}
        return Response(resp, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
def redlist_statistics(request):
    """
    Returns interesting stats about the db
    """
    if request.method == 'GET':
        class_rank = taxa_models.Rank.objects.get(name='Class')
        class_nodes = taxa_models.Taxon.objects.exclude(name='Insecta').filter(rank=class_rank)
        statuses = models.Assessment.REDLIST_CATEGORY_CHOICES
        data = {}
        node_names = [t.name for t in class_nodes]
        node_common_names = [t.get_top_common_name().capitalize() for t in class_nodes]

        for stat_id, stat_value in statuses:
            node_statuses = {}
            for node in class_nodes:
                count = node.get_descendants().filter(assessment__redlist_category=stat_id).count()
                node_statuses[node.name] = count
            data[stat_value] = node_statuses

        insecta = taxa_models.Taxon.objects.filter(name='Insecta', rank=class_rank).first()
        insecta_nodes = taxa_models.Taxon.objects.filter(parent=insecta)
        for i in insecta_nodes:
            node_names.append(i.name)
            node_common_names.append(i.get_top_common_name().capitalize())
        for stat_id, stat_value in statuses:
            node_statuses = {}
            for node in insecta_nodes:
                count = node.get_descendants().filter(assessment__redlist_category=stat_id).count()
                node_statuses[node.name] = count
            data[stat_value].update(node_statuses)

        # Reformat the data dict to be a list of dicts
        reformatted_data = []
        for key, value_dict in data.items():
            reformatted_data.append({key: value_dict})

        import pprint
        pprint.pprint(reformatted_data)

        resp = {'statistics': reformatted_data, 'names': node_names, 'common_names': node_common_names, 'statuses': [s[1] for s in statuses]}
        return Response(resp, status=status.HTTP_202_ACCEPTED)
