from django.conf.urls import url, include
from taxa import views
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.renderers import TemplateHTMLRenderer, BrowsableAPIRenderer, JSONRenderer


urlpatterns = [
    # Browsable API
    url(r'^api/$', views.api_root),
    url(r'^api/detail/(?P<pk>[0-9]+)/$', views.TaxonDetail.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer))),
    url(r'^api/common-name/(?P<pk>[0-9]+)/$', views.CommonNameDetail.as_view()),

    # HTML template views
    url(r'^detail/(?P<pk>[0-9]+)/$', views.TaxonDetail.as_view(renderer_classes=(TemplateHTMLRenderer,)), name='taxa_detail'),
    url(r'^list/$', views.TaxonListView.as_view(), name='search_autocomplete'),

    #url(r'^lineage/(?P<species_name>\w+)/$', views.get_lineage, name='lineage'),
]
urlpatterns = format_suffix_patterns(urlpatterns)