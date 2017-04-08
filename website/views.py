from django.views.generic.base import TemplateView


class IndexView(TemplateView):
    template_name = 'website/index.html'


class AboutView(TemplateView):
    template_name = 'website/about.html'


class SearchView(TemplateView):
    template_name = 'website/main_map.html'


class ExploreView(TemplateView):
    template_name = 'website/tree.html'


class TaxonView(TemplateView):
    template_name = 'website/taxon.html'


class AssessmentView(TemplateView):
    template_name = 'website/assessment.html'


class DistributionView(TemplateView):
    template_name = 'website/distribution.html'


#class MapSearchView(TemplateView):
#    template_name = 'website/main_map.html'