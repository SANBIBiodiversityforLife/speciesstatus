from django.conf.urls import url, include
from biblio import views
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.renderers import TemplateHTMLRenderer, BrowsableAPIRenderer, JSONRenderer


urlpatterns = [
    url(r'^api/biblio-write/(?P<doi>.+?)/$', views.RefList.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer)), name='get_bibtex'),
    url(r'^api/get-bibtex/(?P<doi>.+?)/$', views.get_bibtex, name='get_bibtex'),
    url(r'^api/post-bibtex/$', views.post_bibtex, name='post_bibtex'),
    url(r'^api/detail/(?P<pk>[0-9]+)/$', views.Biblio.as_view(renderer_classes=(BrowsableAPIRenderer, JSONRenderer))),
]
urlpatterns = format_suffix_patterns(urlpatterns)
