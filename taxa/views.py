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
        #'taxa': reverse('lineage', request=request, format=format),
        #'taxon_list': reverse('search_autocomplete', request=request, format=format),
        'taxa': reverse('search_autocomplete', request=request, format=format),
        #'taxon_detail': reverse('detail', request=request, format=format),
    })


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
        ancestors_serializer = serializers.AncestorSerializer(ancestors, many=True)
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
                     'common_names__name')


class ChildrenView(generics.RetrieveAPIView):
    queryset = models.Taxon.objects.all()
    serializer_class = serializers.TaxonChildrenSerializer


def unflatten_tree(flat_tree_data, parent_id = 0):
    children = [x for x in flat_tree_data if x['parent'] == parent_id]
    for child in children:
        child['children'] = unflatten_tree(flat_tree_data, child['id'])
    return children
    # test = [{'id': 1, 'parent_id': 0},{'id': 2, 'parent_id': 0},{'id': 3, 'parent_id': 0},{'id': 4, 'parent_id': 2},{'id': 5, 'parent_id': 4},]


def get_ancestors(ancestors, node):
    if node.parent:
        print(node.parent)
        ancestors.append(node.parent)
        get_ancestors(ancestors, node.parent)
    else:
        return ancestors

class LineageView(generics.RetrieveAPIView):
    queryset = models.Taxon.objects.all()
    serializer_class = serializers.TaxonBasicSerializerWithRank
    template_name = 'website/tree.html'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        ancestors = list(drilldown_tree_for_node(instance))
        #al = []
        #for a in ancestors_old:
        #    al.append(a)
        #ancestors = get_ancestors([instance], instance)
        nodes = []
        for node in ancestors:
            print(node)
            nodes.append(node)
            siblings = node.get_siblings()
            if len(siblings) > 0:
                nodes.extend(siblings)
        nodes_set = list(set(nodes))

        serializer = self.get_serializer(nodes_set, many=True)
        # root = serializer.data[0]
        root = [x for x in serializer.data if x['id'] == ancestors[0].id][0]
        root['children'] = unflatten_tree(serializer.data, ancestors[0].id)

        # How the heck do you access the entire thing in template? no idea, have to make it a param
        if TemplateHTMLRenderer in self.renderer_classes:
            params = {"lineage": JSONRenderer().render(serializer.data), 'pk': instance.id}
            return Response(params)
        else:
            return Response(root)


@api_view(['GET'])
def get_lineage(species_name):
    root = models.Taxon.objects.filter(name=species_name).first()
    ancestors = root.get_ancestors(include_self=True)
    serializer = serializers.TaxonLineageSerializer(ancestors, many=True)
    return Response(serializer.data)
