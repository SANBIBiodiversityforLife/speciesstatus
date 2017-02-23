from django.conf.urls import url, include
from taxa import views
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.renderers import TemplateHTMLRenderer, BrowsableAPIRenderer, JSONRenderer


urlpatterns = [
    # Browsable API
    url(r'^api/$', views.api_root),
    url(r'^api/ancestors/(?P<pk>[0-9]+)/$', views.AncestorsView.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)), name='api_ancestors'),
    url(r'^api/detail/(?P<pk>[0-9]+)/$', views.TaxonDetail.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer))),
    url(r'^api/common-names/(?P<pk>[0-9]+)/$', views.CommonNameList.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)), name='api_common_names'),
    url(r'^api/common-name/(?P<pk>[0-9]+)/$', views.CommonNameDetail.as_view()),
    url(r'^api/lineage/(?P<pk>\d*)/$', views.LineageView.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)), name='api_lineage'),
    url(r'^api/children/(?P<pk>\d*)/$',
        views.ChildrenView.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)),
        name='api_children'),
    url(r'^api/taxon-write/$', views.TaxonWrite.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)), name='api_taxon_write'),
    url(r'^api/description-write/$', views.DescriptionWrite.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)), name='api_description_write'),
    url(r'^api/info-write/$', views.InfoWrite.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)), name='api_info_write'),
    url(r'^api/rank-list/$', views.RankList.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)), name='api_rank_list'),

    # HTML template views
    url(r'^detail/(?P<pk>[0-9]+)/$', views.TaxonDetail.as_view(renderer_classes=(TemplateHTMLRenderer,)), name='taxa_detail'),
    url(r'^list/$', views.TaxonListView.as_view(), name='search_autocomplete'),
    url(r'^lineage/(?P<pk>\d*)/$', views.LineageView.as_view(renderer_classes=(TemplateHTMLRenderer,)), name='lineage_pk'),
    url(r'^distribution/(?P<pk>\d*)/$', views.DistributionList.as_view(renderer_classes=(TemplateHTMLRenderer, JSONRenderer)), name='distribution_list'),
]
urlpatterns = format_suffix_patterns(urlpatterns)