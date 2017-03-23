# from django.contrib import admin
from django.contrib.gis import admin
from taxa import models


admin.site.register(models.Rank)
admin.site.register(models.Taxon)
admin.site.register(models.Description)
admin.site.register(models.CommonName)
admin.site.register(models.GeneralDistribution, admin.GeoModelAdmin)
admin.site.register(models.PointDistribution, admin.GeoModelAdmin)

