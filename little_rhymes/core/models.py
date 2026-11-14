from django.db import models
from poems.validators import image_upload_path, validate_image

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default='Little Rhymes')
    logo = models.ImageField(upload_to=image_upload_path, blank=True, validators=[validate_image])
    hero_title = models.CharField(max_length=200, default='Discover the Magical World of Poems!')
    hero_description = models.CharField(max_length=300, default='Read, Listen, Sing, and Learn Beautiful Poems in Your Favorite Language.')
    hero_image = models.ImageField(upload_to=image_upload_path, blank=True, validators=[validate_image])
    hero_image_alt = models.CharField(max_length=250, blank=True, help_text='Describe a custom homepage illustration for screen-reader users.')
    contact_email = models.EmailField(blank=True)
    footer_description = models.CharField(max_length=300, default='Little poems. Big imaginations. A joyful place to learn, sing and grow together.')

    class Meta:
        verbose_name_plural = 'site settings'
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name='singleton_site_settings')]

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.site_name

class FAQ(models.Model):
    question = models.CharField(max_length=250)
    answer = models.TextField(max_length=3000)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = 'FAQ'

    def __str__(self):
        return self.question

class ContentPage(models.Model):
    slug = models.SlugField(unique=True, help_text='about, privacy, terms, copyright, or resources')
    title = models.CharField(max_length=160)
    introduction = models.CharField(max_length=400, blank=True)
    body = models.TextField(help_text='Plain text. Separate paragraphs with a blank line; HTML is escaped.')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
