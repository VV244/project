from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from poems.models import Poem, Language, ClassLevel, Category

class OriginSitemap(Sitemap):
    protocol = 'https'

    def get_urls(self, page=1, site=None, protocol=None):
        from types import SimpleNamespace
        from urllib.parse import urlsplit
        origin = urlsplit(settings.SITE_URL)
        return super().get_urls(page, site=SimpleNamespace(domain=origin.netloc), protocol=origin.scheme)

class PoemSitemap(OriginSitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Poem.objects.published()

    def lastmod(self, obj):
        return obj.updated_at

class StaticSitemap(OriginSitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return ['home', 'poems:list', 'poems:classes', 'poems:languages', 'poems:categories', 'about', 'resources', 'faq', 'privacy', 'terms', 'copyright']

    def location(self, item):
        return reverse(item)

class TaxonomySitemap(OriginSitemap):
    def items(self):
        return list(Language.objects.filter(is_active=True)) + list(ClassLevel.objects.filter(is_active=True)) + list(Category.objects.filter(is_active=True))
