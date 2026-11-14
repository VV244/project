from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html
from .models import Language, ClassLevel, Category, Poem

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'native_name', 'code', 'text_direction', 'is_active']
    list_filter = ['is_active', 'text_direction']
    search_fields = ['name', 'native_name', 'code']
    prepopulated_fields = {'slug': ['name']}
    list_editable = ['is_active']

@admin.register(ClassLevel)
class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_order', 'is_active']
    list_editable = ['display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ['name']}

@admin.register(Poem)
class PoemAdmin(admin.ModelAdmin):
    list_display = ['title', 'language', 'status', 'is_featured', 'published_at', 'preview_link']
    list_filter = ['status', 'language', 'classes', 'categories', 'is_featured']
    search_fields = ['title', 'poem_text', 'author', 'keywords']
    filter_horizontal = ['classes', 'categories']
    list_select_related = ['language']
    date_hierarchy = 'created_at'
    list_per_page = 25
    save_on_top = True
    readonly_fields = ['created_at', 'updated_at', 'preview_link']
    actions = ['publish', 'unpublish', 'feature', 'unfeature']
    fieldsets = [
        ('Poem', {'fields': ['title', 'slug', 'language', 'classes', 'categories', 'author', 'short_description', 'poem_text']}),
        ('Illustration & media', {'fields': ['thumbnail', 'illustration', 'audio_file', 'video_url']}),
        ('Rights & publication', {'fields': ['rights_statement', 'rights_confirmed', 'status', 'published_at', 'is_featured', 'home_priority', 'preview_link']}),
        ('Search & SEO', {'fields': ['keywords', 'meta_title', 'meta_description'], 'classes': ['collapse']}),
        ('History', {'fields': ['created_at', 'updated_at'], 'classes': ['collapse']}),
    ]

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.published_at:
            fields.append('slug')
        return fields

    @admin.display(description='Preview')
    def preview_link(self, obj):
        return format_html('<a href="{}">Preview poem ↗</a>', reverse('poems:preview', args=[obj.pk])) if obj.pk else 'Save first to preview.'

    @admin.action(description='Publish selected poems (rights required)', permissions=['change'])
    def publish(self, request, queryset):
        count = 0
        for poem in queryset:
            poem.status = Poem.Status.PUBLISHED
            try:
                poem.full_clean()
                poem.save()
                count += 1
            except ValidationError as exc:
                self.message_user(request, f'{poem.title}: {"; ".join(exc.messages)}', messages.ERROR)
        self.message_user(request, f'Published {count} poems.')

    @admin.action(description='Return selected poems to draft', permissions=['change'])
    def unpublish(self, request, queryset):
        queryset.update(status=Poem.Status.DRAFT)

    @admin.action(description='Mark as featured', permissions=['change'])
    def feature(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description='Remove from featured', permissions=['change'])
    def unfeature(self, request, queryset):
        queryset.update(is_featured=False)
