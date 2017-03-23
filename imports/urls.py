from django.conf.urls import url, include
from imports import views
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.renderers import TemplateHTMLRenderer, BrowsableAPIRenderer, JSONRenderer


urlpatterns = [
    url(r'^sis/$', views.sis, name='import_sis'),
    url(r'^sarca/$', views.sarca, name='import_sarca'),
    url(r'^sabca/$', views.sabca_r, name='import_sabca'),
    url(r'^spstatus/$', views.spstatus, name='import_spstatus'),
    url(r'^import-phylums/$', views.import_phylums, name='import_phylums'),
    # url(r'^seakeys/$', views.LineageView.as_view(renderer_classes=(TemplateHTMLRenderer,)), name='lineage_pk'),

]
urlpatterns = format_suffix_patterns(urlpatterns)