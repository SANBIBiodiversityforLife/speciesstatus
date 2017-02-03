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
                     #'info__habitat',
                     'common_names__name')


class ChildrenView(generics.RetrieveAPIView):
    queryset = models.Taxon.objects.all()
    serializer_class = serializers.TaxonBasicSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        children = instance.get_children()
        serializer = self.get_serializer(children, many=True)
        instance_serializer = self.get_serializer(instance)
        return Response({'children': serializer.data, 'parent': instance_serializer.data})


class LineageView(generics.RetrieveAPIView):
    queryset = models.Taxon.objects.all()
    serializer_class = serializers.TaxonBasicSerializer
    template_name = 'website/tree.html'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        ancestors = drilldown_tree_for_node(instance)

        nodes = []
        for node in ancestors:
            nodes.append(node)
            siblings = node.get_siblings()
            if len(siblings) > 0:
                nodes += siblings

        serializer = self.get_serializer(nodes, many=True)

        # How the heck do you access the entire thing in template? no idea, have to make it a param
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
