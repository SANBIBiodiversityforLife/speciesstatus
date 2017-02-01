from django.conf.urls import url, include
from imports import views
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.renderers import TemplateHTMLRenderer, BrowsableAPIRenderer, JSONRenderer


urlpatterns = [
    url(r'^sis/$', views.sis, name='import_sis'),
    # url(r'^seakeys/$', views.LineageView.as_view(renderer_classes=(TemplateHTMLRenderer,)), name='lineage_pk'),

]
urlpatterns = format_suffix_patterns(urlpatterns)