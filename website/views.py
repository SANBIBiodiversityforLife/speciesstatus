from django.views.generic.base import TemplateView


class IndexView(TemplateView):
    template_name = 'website/index.html'


class AboutView(TemplateView):
    template_name = 'website/about.html'


class PartnerView(TemplateView):
    template_name = 'website/partners.html'
