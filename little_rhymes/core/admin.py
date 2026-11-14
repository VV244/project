from django.contrib import admin
from .models import SiteSettings, FAQ, ContentPage

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists() and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'display_order', 'is_active']
    list_editable = ['display_order', 'is_active']
    search_fields = ['question', 'answer']
    list_filter = ['is_active']

@admin.register(ContentPage)
class ContentPageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'updated_at']
    search_fields = ['title', 'body']
    readonly_fields = ['updated_at']
