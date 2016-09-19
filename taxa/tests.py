from django.test import TestCase
from taxa.models import Taxon


class TaxonTestCase(TestCase):
    def setUp(self):
        Taxon.objects.create(name='MyRandomGenus')

    # def test_name_change(self):
    #    temp = Taxon.objects.get(name='MyRandomGenus')
    #    temp.
