from django.contrib import admin
from redlist import models


class AssessmentAdmin(admin.ModelAdmin):
    search_fields = ('taxon__name', 'redlist_category')


class ContributionAdmin(admin.ModelAdmin):
    search_fields = ('assessment__taxon__name', 'person__surname', 'person__first')


class ThreatNatureAdmin(admin.ModelAdmin):
    search_fields = ('assessment__taxon__name', 'threat__name')


# Register your models here.
admin.site.register(models.Assessment, AssessmentAdmin)
admin.site.register(models.ThreatNature, ThreatNatureAdmin)
admin.site.register(models.Contribution, ContributionAdmin)



