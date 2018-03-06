# from django.contrib import admin
from django.contrib.gis import admin
from taxa import models


class TaxonAdmin(admin.ModelAdmin):
    search_fields = ('name', 'rank__name')


class CommonNameAdmin(admin.ModelAdmin):
    search_fields = ('taxon__name', 'name', 'language')


class DescriptionAdmin(admin.ModelAdmin):
    search_fields = ('taxon__name',)


class InfoAdmin(admin.ModelAdmin):
    search_fields = ('taxon__name',)


admin.site.register(models.Rank)
admin.site.register(models.Language)
admin.site.register(models.Info, InfoAdmin)
admin.site.register(models.Taxon, TaxonAdmin)
admin.site.register(models.Description, DescriptionAdmin)
admin.site.register(models.CommonName, CommonNameAdmin)
admin.site.register(models.GeneralDistribution, admin.GeoModelAdmin)
admin.site.register(models.PointDistribution, admin.GeoModelAdmin)

