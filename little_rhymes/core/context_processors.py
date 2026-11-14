from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from poems.models import Language, ClassLevel, Category
from .models import SiteSettings

def site_context(request):
    data = cache.get('navigation')
    if data is None:
        data = {
            'site_settings': SiteSettings.objects.first(),
            'nav_languages': list(Language.objects.filter(is_active=True)),
            'nav_classes': list(ClassLevel.objects.filter(is_active=True)),
            'nav_categories': list(Category.objects.filter(is_active=True)),
        }
        cache.set('navigation', data, 300)
    # Strip query strings from canonical URLs (search/filter pages carry noindex).
    return {**data, 'site_url': settings.SITE_URL, 'canonical_url': settings.SITE_URL + request.path, 'csp_nonce': getattr(request, 'csp_nonce', ''),
            'default_share_image': settings.SITE_URL + '/static/images/social-card.png'}
