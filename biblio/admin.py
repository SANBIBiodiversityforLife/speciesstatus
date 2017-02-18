from django.contrib import admin
from biblio import models



admin.site.register(models.Reference)


class AuthorshipInline(admin.TabularInline):
    model = models.Authorship
    extra = 1


