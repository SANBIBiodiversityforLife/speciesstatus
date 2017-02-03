from django.conf.urls import url, include
from redlist import views
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.renderers import TemplateHTMLRenderer, BrowsableAPIRenderer, JSONRenderer


urlpatterns = [
    # Browsable API
    url(r'^api/$', views.api_root),
    #url(r'^detail/(?P<pk>[0-9]+)/assessment$', views.AssessmentDetail.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)),
    #    name='api_assessment'),
    url(r'^list$', views.AssessmentList.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)),
        name='assessment_list'),

    # HTML template views
    url(r'^detail/(?P<pk>[0-9]+)/$', views.AssessmentDetail.as_view(renderer_classes=(TemplateHTMLRenderer,)),
        name='assessment_detail'),

]
urlpatterns = format_suffix_patterns(urlpatterns)