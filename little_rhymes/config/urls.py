from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from core.sitemaps import PoemSitemap, StaticSitemap, TaxonomySitemap

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include('core.urls')),
    path('', include('poems.urls')),
    path('', include('contact.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': {'poems': PoemSitemap, 'pages': StaticSitemap, 'browse': TaxonomySitemap}}, name='sitemap'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.not_found'
handler500 = 'core.views.server_error'
