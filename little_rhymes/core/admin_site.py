from django.contrib.admin import AdminSite
from django.db.models import Count, Q

class StudioAdminSite(AdminSite):
    site_header = 'Little Rhymes · Studio'
    site_title = 'Little Rhymes Studio'
    index_title = 'Your learning library'

    def each_context(self, request):
        from poems.models import Poem, Language, ClassLevel, Category
        from contact.models import ContactMessage
        context = super().each_context(request)
        stats = []
        if request.path == '/admin/' and request.user.is_active and request.user.is_staff:
            if request.user.has_perm('poems.view_poem'):
                totals = Poem.objects.aggregate(total=Count('id'), published=Count('id', filter=Q(status='published')), drafts=Count('id', filter=Q(status='draft')))
                stats.extend([('Total poems', totals['total']), ('Published poems', totals['published']), ('Draft poems', totals['drafts'])])
            for model, label in [(Language, 'Languages'), (ClassLevel, 'Classes'), (Category, 'Categories'), (ContactMessage, 'Contact messages')]:
                if request.user.has_perm(f'{model._meta.app_label}.view_{model._meta.model_name}'):
                    stats.append((label, model.objects.count()))
        context['studio_stats'] = stats
        return context
