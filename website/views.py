from django.shortcuts import render
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from mptt.templatetags.mptt_tags import cache_tree_children
from taxa import models as taxa_models
from taxa import serializers as taxa_serializers
import json
from rest_framework.renderers import JSONRenderer
from mptt.utils import drilldown_tree_for_node

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.views.generic.base import TemplateView
#import feedparser
#feeds = feedparser.parse('http://johnsmallman.wordpress.com/author/johnsmallman/feed/')


class IndexView(TemplateView):
    template_name = 'website/index.html'


class AboutView(TemplateView):
    template_name = 'website/about.html'

class MapView(TemplateView):
    template_name = 'website/main_map.html'

