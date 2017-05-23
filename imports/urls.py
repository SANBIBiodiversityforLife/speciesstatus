from django.conf.urls import url, include
from imports import views
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.renderers import TemplateHTMLRenderer, BrowsableAPIRenderer, JSONRenderer


urlpatterns = [
    url(r'^sis/$', views.sis, name='import_sis'),
    url(r'^sarca/$', views.sarca, name='import_sarca'), # Includes the distributions
    url(r'^sabca/$', views.sabca_r, name='import_sabca'),
    url(r'^spstatus/$', views.spstatus, name='import_spstatus'),
    url(r'^seakeys/$', views.seakeys, name='import_seakeys'),
    url(r'^lc-birds/$', views.lc_birds, name='lc_birds'),
    url(r'^clean_points/$', views.st_process, name='st_process'),
    url(r'^clean_origin_codes/$', views.clean_origin_codes, name='clean_origin_codes'),

    url(r'^populate-cns/$', views.populate_higher_level_common_names, name='populate_higher_level_common_names'),
    url(r'^convert-criteria/$', views.convert_all_criteria_strings, name='convert_all_criteria_strings'),

    url(r'^reptile-distribs/$', views.reptile_distribs, name='reptile_distribs'),
    url(r'^mammal-distribs/$', views.mammal_distribs, name='mammal_distribs'),
    url(r'^dragonfly-distribs/$', views.dragonfly_distribs, name='dragonfly_distribs'),
    url(r'^bird-distribs/$', views.bird_distribs, name='bird_distribs'),
    url(r'^frog-distribs/$', views.frog_distribs, name='frog_distribs'),
]
urlpatterns = format_suffix_patterns(urlpatterns)