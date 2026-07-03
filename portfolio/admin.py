from django.contrib import admin

from . import models


@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Identity', {'fields': ('name', 'role', 'tagline', 'location', 'email', 'avatar', 'resume')}),
        ('About', {'fields': ('bio',)}),
        ('Links', {'fields': ('scholar_url', 'github_url', 'linkedin_url', 'twitter_url',
                              'huggingface_url', 'orcid_url', 'instagram_url')}),
    )

    def has_add_permission(self, request):
        # Singleton: only allow the one row.
        return not models.Profile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.ResearchArea)
class ResearchAreaAdmin(admin.ModelAdmin):
    list_display = ('title', 'summary', 'order')
    list_editable = ('order',)


@admin.register(models.Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'venue', 'year', 'kind', 'stage', 'featured')
    list_filter = ('kind', 'stage', 'year', 'featured', 'tags')
    list_editable = ('stage', 'featured')
    search_fields = ('title', 'authors', 'venue')
    filter_horizontal = ('tags',)
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'authors', 'venue', 'year', 'month', 'kind', 'stage', 'award',
                           'tldr', 'abstract', 'body', 'image', 'tags', 'featured')}),
        ('Links', {'fields': ('pdf_url', 'arxiv_url', 'code_url', 'project_url',
                              'video_url', 'slides_url', 'bibtex')}),
    )


@admin.register(models.News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('date', 'content')
    search_fields = ('content',)


@admin.register(models.Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'job_title', 'start_date', 'end_date', 'order')
    list_editable = ('order',)


@admin.register(models.ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'handled')
    list_filter = ('handled', 'created_at')
    list_editable = ('handled',)
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False  # messages only arrive via the contact form


@admin.register(models.ElectionBench)
class ElectionBenchAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'results_updated_at')
    readonly_fields = ('results', 'results_updated_at')
    fieldsets = (
        ('Content (edit freely)', {'fields': ('title', 'tagline', 'overview', 'methodology', 'status')}),
        ('Streamed results (updated by the simulation)', {'fields': ('results_updated_at', 'results')}),
    )

    def has_add_permission(self, request):
        return not models.ElectionBench.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('log_name', 'model_a', 'model_b', 'seed', 'game_idx', 'winner_model', 'updated_at')
    list_filter = ('model_a', 'model_b')
    search_fields = ('log_name', 'model_a', 'model_b', 'winner_model')
    readonly_fields = [f.name for f in models.Game._meta.fields]

    def has_add_permission(self, request):
        return False


admin.site.register(models.Tag)

admin.site.site_header = 'Divij Handa — Portfolio admin'
admin.site.site_title = 'Portfolio admin'
admin.site.index_title = 'Manage site content'
