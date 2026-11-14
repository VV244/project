from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .validators import image_upload_path, audio_upload_path, validate_image, validate_audio, validate_video_url, youtube_id

class Language(models.Model):
    name = models.CharField(max_length=80)
    native_name = models.CharField(max_length=80)
    code = models.CharField(max_length=35, unique=True, validators=[RegexValidator(r'^[a-zA-Z]{2,8}(-[a-zA-Z0-9]{1,8})*$', 'Use a BCP 47 language code, e.g. hi or ur-IN.')])
    slug = models.SlugField(unique=True)
    text_direction = models.CharField(max_length=3, choices=[('ltr', 'Left to right'), ('rtl', 'Right to left')], default='ltr')
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        constraints = [models.CheckConstraint(condition=Q(text_direction__in=['ltr', 'rtl']), name='valid_language_direction')]

    def __str__(self):
        return f'{self.name} · {self.native_name}'

    def get_absolute_url(self):
        return reverse('poems:language', args=[self.slug])

class ClassLevel(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['display_order', 'id']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('poems:class', args=[self.slug])

class Category(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=image_upload_path, blank=True, validators=[validate_image])
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('poems:category', args=[self.slug])

class PoemQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status='published', language__is_active=True, published_at__lte=timezone.now())

    def with_relations(self):
        return self.select_related('language').prefetch_related(
            models.Prefetch('classes', queryset=ClassLevel.objects.filter(is_active=True)),
            models.Prefetch('categories', queryset=Category.objects.filter(is_active=True)),
        )

class Poem(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True, help_text='Permanent after first publication. Leave blank to generate.')
    language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name='poems')
    classes = models.ManyToManyField(ClassLevel, related_name='poems')
    categories = models.ManyToManyField(Category, related_name='poems')
    author = models.CharField(max_length=160, blank=True)
    poem_text = models.TextField(max_length=20000)
    thumbnail = models.ImageField(upload_to=image_upload_path, blank=True, validators=[validate_image])
    illustration = models.CharField(max_length=16, default='garden', choices=[('garden', 'Garden'), ('night', 'Night sky'), ('rain', 'Rainy day'), ('numbers', 'Numbers'), ('bird', 'Little bird'), ('books', 'Books')])
    audio_file = models.FileField(upload_to=audio_upload_path, blank=True, validators=[validate_audio])
    video_url = models.URLField(max_length=500, blank=True, validators=[validate_video_url])
    short_description = models.CharField(max_length=300, blank=True)
    keywords = models.CharField(max_length=300, blank=True)
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    rights_statement = models.CharField(max_length=500, help_text='Required: author, license, source and media permissions.')
    rights_confirmed = models.BooleanField(default=False, help_text='Confirm publication rights for text, image, audio and video.')
    is_featured = models.BooleanField(default=False)
    home_priority = models.PositiveSmallIntegerField(default=0, help_text='Editorial popular-picks order. Higher numbers appear first; no visitor tracking is used.')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = PoemQuerySet.as_manager()

    class Meta:
        ordering = ['-published_at', '-id']
        indexes = [models.Index(fields=['status', '-published_at']), models.Index(fields=['language', 'status']), models.Index(fields=['is_featured', 'status'])]
        constraints = [
            models.CheckConstraint(condition=Q(status__in=['draft', 'published']), name='valid_poem_status'),
            models.CheckConstraint(condition=~Q(status='published') | (Q(published_at__isnull=False) & Q(rights_confirmed=True) & ~Q(rights_statement='')), name='published_has_rights_and_date'),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.pk:
            old = type(self).objects.filter(pk=self.pk).values('slug', 'published_at').first()
            if old and old['published_at'] is not None and self.slug != old['slug']:
                raise ValidationError({'slug': 'Published URLs are permanent. Keep the original slug.'})
            if old and old['published_at'] is not None and self.published_at is None:
                raise ValidationError({'published_at': 'Keep the first publication date, even when returning to draft.'})
        if self.status == self.Status.PUBLISHED:
            if not self.rights_confirmed or not self.rights_statement.strip():
                raise ValidationError({'rights_confirmed': 'Confirm all content rights before publishing.'})
            if not self.published_at:
                self.published_at = timezone.now()

    def save(self, *args, **kwargs):
        if not self.slug:
            # Random suffix avoids collisions and supports titles without Latin characters.
            self.slug = f'{slugify(self.title)[:180] or "poem"}-{uuid4().hex[:10]}'
        self.clean()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('poems:detail', args=[self.slug])

    @property
    def youtube_video_id(self):
        return youtube_id(self.video_url) if self.video_url else None

    @property
    def seo_title(self):
        return self.meta_title or self.title

    @property
    def seo_description(self):
        return self.meta_description or self.short_description or f'Read {self.title} in {self.language.name} on Little Rhymes.'
