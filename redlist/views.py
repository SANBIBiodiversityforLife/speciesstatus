from redlist import models
from taxa import models as taxa_models
from redlist import serializers
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework import generics, pagination
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime


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
    serializer_class = serializers.AssessmentSimpleSerializer
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
def redlist_citation(request, pk):
    if request.method == 'GET':
        assessment = models.Assessment.objects.get(pk=pk)
        # taxon = taxa_models.Taxon.objects.get(pk=pk)
        # assessment = taxon.get_latest_assessment()
        contributions = models.Contribution.objects.filter(assessment=assessment, type=models.Contribution.ASSESSOR)
        author_strings = []
        for c in contributions:
            author_string = c.person.surname
            if c.person.first:
                author_string += c.person.first[0]
            author_string += '.'
            author_strings.append(author_string)

        resp =  ', '.join(author_strings) + ' ' +  str(assessment.date.year) + '. A conservation assessment of <em>' + \
               assessment.taxon.name + '</em> ' + assessment.taxon.rank.name.lower() + '.'

        class_rank = taxa_models.Rank.objects.get(name='Class')
        class_ = assessment.taxon.get_ancestors().get(rank=class_rank).name.lower()
        if class_ == 'mammalia':
            resp += ' <strong>In Child MF, Roxburgh L, Do Linh San E, Raimondo D, Davies-Mostert HT, editors. The Red List of Mammals of South Africa, Swaziland and Lesotho. South African National Biodiversity Institute and Endangered Wildlife Trust, South Africa.</strong>'
        elif class_ == 'reptilia':
            resp += ' <strong>In M.F. Bate, W.R. Branch, A.M. Bauer, M. Burger, J. Marais, G.J. Alexander & M.S. de Villiers (eds), Atlas and Red List of Reptiles of South Africa, Lesotho and Swaziland. Suricata 1. South African National Biodiversity Institute, Pretoria.</strong>'
        elif class_ == 'aves':
            resp += ' <strong>In The Eskom Red Data Book of Birds of South Africa, Lesotho and Swaziland. Taylor, MR, Peacock F, Wanless RW (eds). BirdLife South Africa, Johannesburg, South Africa.</strong>'
        elif class_ == 'actinopterygii' or class_ == 'elasmobranchii' or class_ == 'holocephali':
            resp += ' <strong>Seakeys species page.</strong>'
        elif class_ == 'insecta':
            order_rank = taxa_models.Rank.objects.get(name='Order')
            order = assessment.taxon.get_ancestors().get(rank=order_rank).name.lower()
            if order == 'lepidoptera':
                resp += ' <strong>In Mecenero, S., Ball, J.B., Edge, D.A., Hamer, M.L., Henning, G.A., Kruger, M., Pringle, E.L., Terblanche, R.F. & Williams, M.C. (eds). 2013. Conservation assessment of butterflies of South Africa, Lesothos and Swaziland: Red List and atlas. Saftronics (Pty) Ltd., Johannesburg & Animal Demography Unit, Cape Town.</strong>'
            elif order == 'odonata':
                resp += ' <strong>SAMWAYS, M.J. & SIMAIKA, J.P. 2016. Manual of Freshwater Assessment for South Africa: Dragonfly Biotic Index. Suricata 2. South African National Biodiversity Institute, Pretoria.</strong>'

        resp += ' National Assessment: Red List of South Africa version 2017.1 from Species African Species Information &amp; Red Lists. Accessed on ' + datetime.now().strftime("%Y/%m/%d") + '.'

        return Response(resp, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
def redlist_statistics(request):
    """
    Returns interesting stats about the db
    """
    if request.method == 'GET':
        class_rank = taxa_models.Rank.objects.get(name='Class')
        class_nodes = taxa_models.Taxon.objects.exclude(name__in=['Insecta', 'Holocephali']).filter(rank=class_rank) # , 'Elasmobranchii''Holocephali'
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
