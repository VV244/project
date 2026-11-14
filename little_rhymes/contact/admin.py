from django.contrib import admin
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'name', 'created_at', 'is_resolved']
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['subject', 'name', 'email', 'message']
    readonly_fields = ['name', 'email', 'subject', 'message', 'created_at']
    actions = ['resolve', 'reopen']
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    @admin.action(description='Mark selected messages resolved', permissions=['change'])
    def resolve(self, request, queryset):
        queryset.update(is_resolved=True)

    @admin.action(description='Reopen selected messages', permissions=['change'])
    def reopen(self, request, queryset):
        queryset.update(is_resolved=False)
