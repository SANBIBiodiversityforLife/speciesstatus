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
    url(r'^api/info-write/$', views.InfoWrite.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)), name='api_info_write'),
    url(r'^api/cn-write/$', views.CommonNameWrite.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)), name='api_cn_write'),
    url(r'^api/rank-list/$', views.RankList.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)), name='api_rank_list'),

    url(r'^api/alphabetical-genera/(?P<class>[A-Za-z]+)/(?P<letter>[A-Z])/$', views.AlphabeticalGeneraList.as_view(), name='api_genera_list_default'),

    url(r'^api/category-list/(?P<category>[A-Z][A-Z])/$', views.CategoryList.as_view(), name='api_category_list_default'),
    # url(r'^api/category-list/(?P<category>[A-Z][A-Z])/$', views.CategoryList.as_view(), name='api_category_list'),

    url(r'^api/description-format-write/$', views.create_taxon_authority, name='api_descrip_write'),
    url(r'^api/get-taxa-group-list/$', views.get_taxa_group_list, name='api_get_taxa_group_list'),
    url(r'^api/get-distributions/$', views.get_distributions_from_polygon, name='api_get_taxa_in_polygon'),
    url(r'^get-images/(?P<pk>\d*)/$', views.get_images_for_species, name='api_get_images'),

    # HTML template views
    url(r'^detail/(?P<pk>[0-9]+)/$', views.TaxonDetail.as_view(renderer_classes=(TemplateHTMLRenderer,)), name='taxa_detail'),
    url(r'^list/$', views.TaxonListView.as_view(renderer_classes=(TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer)), name='search_autocomplete'),
    url(r'^lineage/(?P<pk>\d*)/$', views.LineageView.as_view(renderer_classes=(TemplateHTMLRenderer,)), name='lineage_pk'),
    url(r'^distribution/(?P<pk>\d*)/$', views.DistributionList.as_view(renderer_classes=(TemplateHTMLRenderer, JSONRenderer)), name='distribution_list_polygon'),
    url(r'^distribution/point/(?P<pk>\d*)/$', views.PointDistributionList.as_view(renderer_classes=(TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer)), name='distribution_list'),
]
urlpatterns = format_suffix_patterns(urlpatterns)