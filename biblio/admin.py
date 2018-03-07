from django.contrib import admin
from biblio import models


class ReferenceAdmin(admin.ModelAdmin):
    search_fields = ('title', 'year', 'doi')


admin.site.register(models.Reference, ReferenceAdmin)


class AuthorshipInline(admin.TabularInline):
    model = models.Authorship
    extra = 1


admin.site.register(models.Authorship)
