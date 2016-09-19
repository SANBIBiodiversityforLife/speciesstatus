from django.contrib import admin
from biblio import models


admin.site.register(models.Publisher)
admin.site.register(models.Journal)

admin.site.register(models.Thesis)
admin.site.register(models.WebPage)
admin.site.register(models.Reference)


class AuthorshipInline(admin.TabularInline):
    model = models.Authorship
    extra = 1


class BookAdmin(admin.ModelAdmin):
    inlines = (AuthorshipInline,)


class JournalArticleAdmin(admin.ModelAdmin):
    inlines = (AuthorshipInline,)


admin.site.register(models.Book, BookAdmin)
admin.site.register(models.JournalArticle, JournalArticleAdmin)
