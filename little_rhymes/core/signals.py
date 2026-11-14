from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from poems.models import Language, ClassLevel, Category
from .models import SiteSettings

@receiver(post_save)
@receiver(post_delete)
def invalidate_navigation(sender, **kwargs):
    if sender in (Language, ClassLevel, Category, SiteSettings):
        cache.delete('navigation')
