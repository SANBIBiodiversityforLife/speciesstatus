"""species URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from website import views as website_views
from taxa import views as taxa_views
from taxa import models as taxa_models

from rest_framework import routers, serializers, viewsets


# Serializers define the API representation
class TaxonSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = taxa_models.Taxon
        fields = ('name', 'author', 'rank', 'reference')


# ViewSets define the view behavior
class TaxonViewSet(viewsets.ModelViewSet):
    queryset = taxa_models.Taxon.objects.all()
    serializer_class = TaxonSerializer


# Routers provide an easy way of automatically determining the URL conf
router = routers.DefaultRouter()
router.register(r'species', TaxonViewSet)


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # Wire up our API using automatic URL routing
    url(r'api/^', include(router.urls)),

    # Include login URLs for the browsable API
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Import of content
    url(r'^taxa/import-seakeys$', taxa_views.import_seakeys, name='import_seakeys'),

    # Index
    url(r'^$', website_views.index, name='index'),
]
