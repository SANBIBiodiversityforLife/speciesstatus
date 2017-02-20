from taxa import models
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.views import APIView
from taxa import serializers
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import filters
from rest_framework import mixins
from mptt.utils import drilldown_tree_for_node


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'taxa': reverse('search_autocomplete', request=request, format=format),
        'distributions': reverse('distribution_list', request=request, format=format),
    })


class DistributionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.GeneralDistribution.objects.all()
    serializer_class = serializers.DistributionSerializer


class DistributionList(generics.ListCreateAPIView):
    serializer_class = serializers.DistributionSerializer
    template_name = 'website/distribution.html'

    def get_queryset(self):
        """
        This view should return a list of all the distribution objects for a taxon, or all distributions
        """
        if self.kwargs['pk'] is not None:
            return models.GeneralDistribution.objects.filter(taxon=self.kwargs['pk'])
        else:
            return models.GeneralDistribution.objects.all()


class CommonNameList(generics.ListCreateAPIView):
    serializer_class = serializers.CommonNameSerializer

    def get_queryset(self):
        """
        This view should return a list of all the common names for a taxon, or all common names
        """
        if self.kwargs['pk'] is not None:
            return models.CommonName.objects.filter(taxon=self.kwargs['pk'])
        else:
            return models.CommonName.objects.all()


class CommonNameDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.CommonName.objects.all()
    serializer_class = serializers.CommonNameSerializer


class TaxonDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Taxon.objects.all()
    serializer_class = serializers.TaxonInfoSerializer
    template_name = 'website/taxon.html'


class TaxonListView(generics.ListAPIView):
    """ Used by the ajax search function """
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
                     'common_names__name')


class ChildrenView(generics.RetrieveAPIView):
    queryset = models.Taxon.objects.all()
    serializer_class = serializers.TaxonChildrenSerializer


def unflatten_tree(flat_tree_data, parent_id = 0):
    """
    Recursively walks through a flat list of nodes and nests them based on parent ids
    :param flat_tree_data: A flat list of nodes with a 'parent' value which is a parent id
    :param parent_id: The ID of the current parent searching for in the list
    :return: Nested dictionaries { id: 1, children: {id: 2, children: {id: 3, etc....
    """
    children = [x for x in flat_tree_data if x['parent'] == parent_id]
    for child in children:
        child['children'] = unflatten_tree(flat_tree_data, child['id'])
    return children


class AncestorsView(generics.RetrieveAPIView):
    queryset = models.Taxon.objects.all()
    serializer_class = serializers.TaxonBasicSerializerWithRank

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Retrieve a flat list of all nodes in the lineage
        ancestors = list(drilldown_tree_for_node(instance))

        # Serialize them all
        serializer = self.get_serializer(ancestors, many=True)
        return Response(serializer.data)


class LineageView(generics.RetrieveAPIView):
    """
    Retrieves a complete lineage of a node in the taxon tree,
    and the siblings of each node in the lineage. Used to build a jstree.
    """
    queryset = models.Taxon.objects.all()
    serializer_class = serializers.TaxonBasicSerializerWithRank
    template_name = 'website/tree.html'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Retrieve a flat list of all nodes in the lineage
        ancestors = list(drilldown_tree_for_node(instance))

        # Loop through them and add the siblings to a flat list of nodes
        nodes = []
        for node in ancestors:
            nodes.append(node)
            siblings = node.get_siblings()
            if len(siblings) > 0:
                nodes.extend(siblings)
        nodes_set = list(set(nodes))

        # Serialize them all
        serializer = self.get_serializer(nodes_set, many=True)

        # Get the root node - this is always Life and always the first node in the ancestors
        root = [x for x in serializer.data if x['id'] == ancestors[0].id][0]

        # Unflatten the serialized list of nodes - so each node will have a "children" value which contains all
        # children for that node
        root['children'] = unflatten_tree(serializer.data, ancestors[0].id)

        # Pass the information either to the HTML differently, along with the pk
        if TemplateHTMLRenderer in self.renderer_classes:
            params = {"lineage": JSONRenderer().render(serializer.data), 'pk': instance.id}
            return Response(params)
        else:
            return Response(root)
