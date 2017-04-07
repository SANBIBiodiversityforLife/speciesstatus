from django.conf.urls import url, include
from redlist import views
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.renderers import TemplateHTMLRenderer, BrowsableAPIRenderer, JSONRenderer


urlpatterns = [
    # Browsable API
    url(r'^api/$', views.api_root),
    #url(r'^detail/(?P<pk>[0-9]+)/assessment$', views.AssessmentDetail.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)),
    #    name='api_assessment'),
    url(r'^list/$', views.AssessmentList.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)),
        name='assessment_list'),
    url(r'^api/assessment-write/$', views.AssessmentWrite.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)),
        name='assessment_write'),
    url(r'^api/contribution-write/$', views.ContributionWrite.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)),
        name='contribution_write'),

    # HTML template views
    url(r'^detail/(?P<pk>[0-9]+)/$', views.AssessmentDetail.as_view(renderer_classes=(TemplateHTMLRenderer, JSONRenderer)),
        name='assessment_detail'),
    url(r'^last-assessment/(?P<taxon_pk>[0-9]+)/$', views.LastAssessmentDetail.as_view(renderer_classes=(TemplateHTMLRenderer, JSONRenderer)),
        name='last_assessment_detail'),
    url(r'^statistics/$', views.redlist_statistics, name='redlist_statistics'),
    url(r'^citation/(?P<pk>[0-9]+)/$', views.redlist_citation, name='redlist_citation'),

]
urlpatterns = format_suffix_patterns(urlpatterns)