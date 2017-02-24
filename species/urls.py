"""species URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from website import views as website_views
from imports import views as imports_views
from people import views as people_views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # Include login URLs for the browsable API
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    #url(r'^api/', website_views.api_root, name='api_root'),

    # Import of content
    # url(r'^taxa/import-seakeys$', taxa_views.import_seakeys, name='import_seakeys'),
    url(r'^import/', include('imports.urls')),

    url(r'^taxa/', include('taxa.urls')),
    url(r'^biblio/', include('biblio.urls')),
    url(r'^assessment/', include('redlist.urls')),
    url(r'^api/people/', people_views.PeopleList.as_view(), name='api_people'),

    # Index
    url(r'^$', website_views.IndexView.as_view(), name='index'),
    url(r'^about/$', website_views.AboutView.as_view(), name='about'),
]
