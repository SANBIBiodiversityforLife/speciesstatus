from taxa import models, helpers
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from taxa import serializers
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework import generics, pagination
from rest_framework.response import Response
from rest_framework import filters
from mptt.utils import drilldown_tree_for_node
import os
from django.conf import settings
import pyexifinfo as p


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'taxa-search': reverse('search_autocomplete', request=request, format=format),
        'rank-list - Get a list of all taxonomic ranks': reverse('api_rank_list', request=request, format=format),
        'taxon-write - Write taxa into the taxa tree': reverse('api_taxon_write', request=request, format=format),
        'info-write - Write non-taxonomic information': reverse('api_info_write', request=request, format=format),
        'common-name-write - Write common names information': reverse('api_cn_write', request=request, format=format),
        'alphabetical list of species by genus': reverse('api_genera_list_default', request=request, format=format),
        'alphabetical list of species by redlist category': reverse('api_category_list_default', request=request, format=format),
        # 'distributions': reverse('distribution_list', request=request, format=format),
    })


@api_view(['GET'])
def get_images_for_species(request, pk):
    taxon = models.Taxon.objects.get(pk=pk)
    class_rank = models.Rank.objects.get(name='Class')
    folder = taxon.get_ancestors().get(rank=class_rank).name.lower()
    if folder == 'actinopterygii' or folder == 'elasmobranchii' or folder == 'holocephali':
        folder = 'fish'
    if folder == 'insecta':
        order_rank = models.Rank.objects.get(name='Order')
        folder = taxon.get_ancestors().get(rank=order_rank).name.lower()
    taxon = taxon.name.lower()
    file_name_template = taxon.replace(' ', '_')
    file_location = os.path.join(settings.BASE_DIR, 'website', 'static', 'sp-imgs', folder, file_name_template)
    # Check the file exists, and then extract the IPTC information embedded in the image for attribution & copyright
    # 'thumb': 'sp-imgs/' + taxon.replace(' ', '_') + '__thumb.jpg' - might need to do this later
    i = 1
    file_info = []

    while(os.path.isfile(file_location + '_' + str(i) + '.jpg')):
        file_name = file_name_template + '_' + str(i) + '.jpg'
        info = p.get_json(file_location + '_' + str(i) + '.jpg')
        return_data = {'file': 'sp-imgs/' + folder + '/' + file_name}
        return_data['author'] = 'Unknown' if 'IPTC:By-line' not in info[0] else info[0]['IPTC:By-line']
        return_data['copyright'] = '[None given]' if 'IPTC:CopyrightNotice' not in info[0] else info[0]['IPTC:CopyrightNotice']
        return_data['source'] = '' if 'IPTC:Source' not in info[0] else info[0]['IPTC:Source']
        file_info.append(return_data)
        i += 1

    if file_info:
        return Response(file_info, status=status.HTTP_202_ACCEPTED)
    else:
        return Response(False, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
def get_distributions_from_polygon(request):
    import pdb; pdb.set_trace()


class LargePagination(pagination.PageNumberPagination):
    page_size = 20


@api_view(['GET'])
def get_taxa_group_list(request):
    """Utility function used to retrieve a list of the taxa groups"""
    if request.method == 'GET':
        class_rank = models.Rank.objects.get(name='Class')
        class_nodes = models.Taxon.objects.values_list('name', flat=True).filter(rank=class_rank).order_by('name')
        return Response(class_nodes, status=status.HTTP_202_ACCEPTED)


class AlphabeticalGeneraList(generics.ListCreateAPIView):
    """An alphabetical listing of genera, used in the explore tab"""
    serializer_class = serializers.TaxonBasicSerializerWithRank
    pagination_class = LargePagination

    def get_queryset(self):
        letter = 'A' if 'letter' not in self.kwargs else self.kwargs['letter']
        class_name = 'Aves' if 'class' not in self.kwargs else self.kwargs['class']
        class_node = models.Taxon.objects.get(name=class_name)

        species_rank = models.Rank.objects.get(name='Species')
        subspecies_rank = models.Rank.objects.get(name='Subspecies')
        return class_node.get_descendants().filter(name__startswith=letter, rank__in=[species_rank, subspecies_rank]).order_by('name')


class CategoryList(generics.ListCreateAPIView):
    """A list of species by redlist category, used in the explore tab"""
    serializer_class = serializers.TaxonBasicSerializerWithRank
    pagination_class=LargePagination

    def get_queryset(self):
        category = 'LC' if 'category' not in self.kwargs else self.kwargs['category']
        species_rank = models.Rank.objects.get(name='Species')
        subspecies_rank = models.Rank.objects.get(name='Subspecies')
        return models.Taxon.objects.filter(assessment__redlist_category=category, rank__in=[species_rank, subspecies_rank]).order_by('name')


@api_view(['GET', 'POST'])
def create_taxon_authority(request):
    """
    Takes in a taxon description reference such as (Johaadien & Khatieb, 2008), and creates a reference
    """
    if request.method == 'POST':
        taxon = models.Taxon.objects.get(pk=request.data['taxon_pk'])
        a_s = request.data['author_string']
        desc, created = helpers.create_taxon_description(authority=str(request.data['author_string']), taxon=taxon)
        desc_s = serializers.DescriptionWriteSerializer(desc)
        if created:
            return Response(desc_s.data, status=status.HTTP_202_ACCEPTED)
        else:
            return Response(desc_s.data, status=status.HTTP_201_CREATED)

    #helpers.create_taxon_description(request['data'],


class RankList(generics.ListCreateAPIView):
    queryset=models.Rank.objects.all()
    serializer_class = serializers.RankSerializer


class TaxonWrite(generics.ListCreateAPIView):
    queryset = models.Taxon.objects.all()
    serializer_class = serializers.TaxonWriteSerializer

    # Overriding super method to use .get_or_create() instead of .save()
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(): # raise_exception=True in super
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            try:
                taxon = models.Taxon.objects.get(**serializer.data)
                taxon = serializers.TaxonWriteSerializer(taxon)
                return Response(taxon.data, status=status.HTTP_202_ACCEPTED)
            except models.Taxon.DoesNotExist:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommonNameWrite(generics.ListCreateAPIView):
    queryset = models.CommonName.objects.all()
    serializer_class = serializers.CommonNameWriteSerializer


class InfoWrite(generics.ListCreateAPIView):
    queryset = models.Info.objects.all()
    serializer_class = serializers.InfoWriteSerializer


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


class PointDistributionList(generics.ListCreateAPIView):
    pagination_class = None
    serializer_class = serializers.PointSerializer
    template_name = 'website/distribution.html'

    def get_queryset(self):
        """
        This view should return a list of all the distribution points for a taxon, or all distributions
        """
        if self.kwargs['pk'] is not None:
            return models.PointDistribution.objects.filter(taxon=self.kwargs['pk'])
        else:
            return models.PointDistribution.objects.all()


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

    def get_queryset(self):
        species_rank = models.Rank.objects.get(name='Species')
        subspecies_rank = models.Rank.objects.get(name='Subspecies')
        return models.Taxon.objects.filter(rank__in=[species_rank, subspecies_rank], assessment__isnull=False)

    serializer_class = serializers.TaxonBasicSerializerWithRank
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',
                     'info__morphology',
                     'info__diagnostics',
                     'info__movement',
                     'info__reproduction',
                     'info__trophic',
                     'common_names__name')
    template_name = 'website/search.html'



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
