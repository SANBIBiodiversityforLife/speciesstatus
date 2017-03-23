from django.conf.urls import url, include
from imports import views
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.renderers import TemplateHTMLRenderer, BrowsableAPIRenderer, JSONRenderer


urlpatterns = [
    url(r'^sis/$', views.sis, name='import_sis'),
    url(r'^sarca/$', views.sarca, name='import_sarca'),
    url(r'^sabca/$', views.sabca_r, name='import_sabca'),
    url(r'^spstatus/$', views.spstatus, name='import_spstatus'),
    url(r'^seakeys/$', views.seakeys, name='import_seakeys'),
    url(r'^bird-distribs/$', views.insert_bird_distrib_data, name='insert_bird_distrib_data'),
    url(r'^import-phylums/$', views.import_phylums, name='import_phylums'),
    url(r'^populate-imgs/$', views.download_missing_images, name='download_missing_images'),
    url(r'^populate-cns/$', views.populate_higher_level_common_names, name='populate_higher_level_common_names'),
    url(r'^dragon-distribs/$', views.load_dragonfly_distribs, name='load_dragonfly_distribs'),
    # url(r'^seakeys/$', views.LineageView.as_view(renderer_classes=(TemplateHTMLRenderer,)), name='lineage_pk'),

]
urlpatterns = format_suffix_patterns(urlpatterns)