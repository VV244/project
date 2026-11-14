import io
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User, Permission
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from core.models import ContentPage
from .models import Poem, Language, ClassLevel, Category
from .validators import validate_audio, validate_image, validate_video_url, youtube_id

class LibraryFixture(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.en = Language.objects.create(name='English', native_name='English', code='en', slug='english')
        cls.hi = Language.objects.create(name='Hindi', native_name='हिन्दी', code='hi', slug='hindi')
        cls.ur = Language.objects.create(name='Urdu', native_name='اردو', code='ur', slug='urdu', text_direction='rtl')
        cls.kg = ClassLevel.objects.create(name='Junior KG', slug='junior-kg')
        cls.one = ClassLevel.objects.create(name='Class 1', slug='class-1')
        cls.nature = Category.objects.create(name='Nature Poems', slug='nature-poems')
        cls.animals = Category.objects.create(name='Animal Poems', slug='animal-poems')
        cls.sun = cls.make_poem('Sunshine', 'sunshine', cls.en, 'A little sunshine.\nA little seed.', author='Demo Writer')
        cls.sun.classes.set([cls.kg, cls.one]); cls.sun.categories.set([cls.nature])
        cls.bird = cls.make_poem('नन्ही चिड़िया', 'nanhi-chidiya', cls.hi, 'नन्ही चिड़िया गाना गाए।')
        cls.bird.classes.set([cls.one]); cls.bird.categories.set([cls.animals, cls.nature])
        cls.urdu = cls.make_poem('ننھا ستارہ', 'urdu-star', cls.ur, 'ننھا تارا چمکے رات۔')
        cls.urdu.classes.set([cls.kg]); cls.urdu.categories.set([cls.nature])
        cls.draft = cls.make_poem('Secret draft', 'secret-draft', cls.en, 'Unpublished.', status='draft')
        cls.future = cls.make_poem('Future poem', 'future-poem', cls.en, 'Not yet.', published_at=timezone.now()+timedelta(days=2))
        for slug in ['about', 'privacy', 'terms', 'copyright', 'resources']:
            ContentPage.objects.create(slug=slug, title=slug.title(), body='A helpful page.')

    @classmethod
    def make_poem(cls, title, slug, language, text, **kwargs):
        data = {'title': title, 'slug': slug, 'language': language, 'poem_text': text,
                'rights_statement': 'Original test material', 'rights_confirmed': True,
                'status': 'published', 'published_at': timezone.now()-timedelta(hours=1)}
        data.update(kwargs)
        if data['status'] == 'draft' and 'published_at' not in kwargs:
            data['published_at'] = None
        return Poem.objects.create(**data)

    def setUp(self):
        cache.clear()

class PublicPageTests(LibraryFixture):
    def test_home(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Discover the Magical World of Poems!')
        self.assertContains(response, self.sun.title)
        self.assertNotContains(response, 'Secret draft')
        self.assertNotContains(response, 'Future poem')

    def test_all_navigation_pages(self):
        for url in ['/poems/', '/classes/', '/languages/', '/categories/', '/about/', '/contact/', '/privacy/', '/terms/', '/copyright/', '/faq/', '/resources/', '/favorites/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_class_page(self):
        response = self.client.get(self.kg.get_absolute_url())
        self.assertEqual({p.pk for p in response.context['page_obj']}, {self.sun.pk, self.urdu.pk})

    def test_class_filter(self):
        response = self.client.get('/poems/', {'class_level': 'junior-kg'})
        self.assertEqual(response.context['page_obj'].paginator.count, 2)

    def test_language_page_and_filter(self):
        for url, params in [(self.hi.get_absolute_url(), {}), ('/poems/', {'language': 'hindi'})]:
            response = self.client.get(url, params)
            self.assertEqual([p.pk for p in response.context['page_obj']], [self.bird.pk])

    def test_category_page_and_filter(self):
        for url, params in [(self.animals.get_absolute_url(), {}), ('/poems/', {'category': 'animal-poems'})]:
            response = self.client.get(url, params)
            self.assertEqual([p.pk for p in response.context['page_obj']], [self.bird.pk])

    def test_combined_filters(self):
        response = self.client.get('/poems/', {'class_level': 'class-1', 'language': 'hindi', 'category': 'animal-poems', 'q': 'चिड़िया'})
        self.assertEqual([p.pk for p in response.context['page_obj']], [self.bird.pk])

    def test_search_title_text_keywords_author_and_language(self):
        self.sun.keywords = 'garden blossom'; self.sun.save()
        for query, pk in [('Sunshine', self.sun.pk), ('seed', self.sun.pk), ('blossom', self.sun.pk), ('Demo Writer', self.sun.pk), ('हिन्दी', self.bird.pk)]:
            with self.subTest(query=query):
                response = self.client.get('/poems/', {'q': query})
                self.assertIn(pk, [p.pk for p in response.context['page_obj']])

    def test_distinct_search_results_across_many_to_many(self):
        self.assertEqual(self.client.get('/poems/', {'q': 'Poems'}).context['page_obj'].paginator.count, 3)

    def test_unknown_filter_and_long_search_handled(self):
        for params in [{'language': 'missing'}, {'sort': 'drop table'}, {'q': 'a'*121}]:
            response = self.client.get('/poems/', params)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['filter_form'].errors)
            self.assertEqual(response.context['page_obj'].paginator.count, 0)

    def test_fixed_class_scope_cannot_be_overridden(self):
        response = self.client.get(self.kg.get_absolute_url(), {'class_level': 'class-1'})
        self.assertEqual({p.pk for p in response.context['page_obj']}, {self.sun.pk, self.urdu.pk})

    def test_empty_state(self):
        self.assertContains(self.client.get('/poems/', {'q': 'nothing-matches'}), 'No little rhymes here yet')

    def test_sorting_and_pagination_preserve_filters(self):
        for i in range(15):
            self.make_poem(f'Extra {i:02}', f'extra-{i}', self.en, 'Original text')
        response = self.client.get('/poems/', {'language': 'english', 'sort': 'title'})
        self.assertEqual(len(response.context['page_obj']), 12)
        self.assertContains(response, 'language=english&amp;sort=title&amp;page=2')
        next_page = self.client.get('/poems/', {'language': 'english', 'sort': 'title', 'page': 2})
        self.assertEqual(len(next_page.context['page_obj']), 4)
        self.assertEqual(self.client.get('/poems/', {'page': 'invalid'}).status_code, 200)

    def test_poem_detail_and_unicode_rtl(self):
        response = self.client.get(self.urdu.get_absolute_url())
        self.assertContains(response, 'dir="rtl"')
        self.assertContains(response, 'ننھا ستارہ')
        self.assertContains(self.client.get(self.bird.get_absolute_url()), 'नन्ही चिड़िया')

    def test_draft_and_scheduled_poems_hidden_everywhere(self):
        for poem in [self.draft, self.future]:
            self.assertEqual(self.client.get(poem.get_absolute_url()).status_code, 404)
            self.assertEqual(self.client.get(reverse('poems:api-detail', args=[poem.slug])).status_code, 404)
            self.assertNotContains(self.client.get('/sitemap.xml'), poem.get_absolute_url())

    def test_inactive_language_hides_poems_and_routes(self):
        self.hi.is_active = False; self.hi.save()
        self.assertEqual(self.client.get(self.hi.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.get(self.bird.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get('/'), self.bird.title)

    def test_missing_object_404(self):
        self.assertEqual(self.client.get('/poems/not-here/').status_code, 404)
        self.assertEqual(self.client.get('/classes/not-here/').status_code, 404)

    @override_settings(DEBUG=False)
    def test_custom_404(self):
        response = self.client.get('/not-a-real-page/', secure=True)
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'This rhyme wandered off.', status_code=404)

    def test_escaped_poem_and_structured_data(self):
        self.sun.poem_text = '</script><script>alert("xss")</script>'; self.sun.save()
        response = self.client.get(self.sun.get_absolute_url())
        self.assertNotContains(response, '<script>alert(')
        self.assertContains(response, '&lt;script&gt;')
        self.assertContains(response, '\\u003c/script\\u003e')
        import json, re
        data = json.loads(re.search(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', response.content.decode(), re.S).group(1))
        self.assertEqual(data['inLanguage'], 'en')

    def test_security_headers(self):
        response = self.client.get('/')
        self.assertIn("object-src 'none'", response['Content-Security-Policy'])
        self.assertIn('microphone=()', response['Permissions-Policy'])
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')

    def test_xml_sitemap_and_robots(self):
        self.assertContains(self.client.get('/sitemap.xml'), self.sun.get_absolute_url())
        self.assertContains(self.client.get('/robots.txt'), 'Disallow: /admin/')

    def test_health(self):
        self.assertEqual(self.client.get('/health/').json(), {'status': 'ok'})

    def test_query_count_does_not_grow_with_cards(self):
        self.client.get('/')  # Warm shared navigation cache.
        for i in range(12):
            poem = self.make_poem(f'Poem {i}', f'bounded-{i}', self.en, 'A poem')
            poem.classes.set([self.kg, self.one]); poem.categories.set([self.nature, self.animals])
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get('/poems/')
            self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 7, '\n'.join(q['sql'] for q in queries))

    def test_interface_translation_independent_from_poem_language(self):
        self.client.post('/i18n/setlang/', {'language': 'hi', 'next': self.sun.get_absolute_url()})
        response = self.client.get(self.sun.get_absolute_url())
        self.assertContains(response, 'मुखपृष्ठ')
        self.assertContains(response, 'A little sunshine.')
        self.assertContains(response, 'lang="en"')

class APITests(LibraryFixture):
    def test_readonly_paginated_api(self):
        response = self.client.get('/api/poems/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 3)
        self.assertEqual(self.client.post('/api/poems/', {}).status_code, 405)

    def test_filters_and_favorites_ids(self):
        self.assertEqual(self.client.get('/api/poems/', {'ids': str(self.sun.pk)}).json()['count'], 1)
        response = self.client.get('/api/poems/', {'language': 'hindi', 'class_level': 'class-1', 'category': 'animal-poems'})
        self.assertEqual(response.json()['results'][0]['slug'], self.bird.slug)

    def test_invalid_api_inputs(self):
        for params in [{'ids': 'x'}, {'ids': '1,'}, {'language': 'missing'}, {'ids': '1,'*101+'1'}]:
            self.assertEqual(self.client.get('/api/poems/', params).status_code, 400)

    def test_detail_api_unicode_and_no_private_fields(self):
        data = self.client.get('/api/poems/nanhi-chidiya/').json()
        self.assertEqual(data['title'], self.bird.title)
        self.assertNotIn('rights_confirmed', data)

class AdminTests(LibraryFixture):
    def test_anonymous_and_nonstaff_denied(self):
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        user = User.objects.create_user('visitor', password='secure-test-password')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/admin/').status_code, 302)

    def test_staff_without_permissions_cannot_preview(self):
        user = User.objects.create_user('staff', is_staff=True)
        self.client.force_login(user)
        response = self.client.get(reverse('poems:preview', args=[self.draft.pk]))
        self.assertEqual(response.status_code, 403)

    def test_view_permission_does_not_grant_edit(self):
        user = User.objects.create_user('reader', is_staff=True)
        user.user_permissions.add(Permission.objects.get(codename='view_poem'))
        self.client.force_login(user)
        self.assertEqual(self.client.get('/admin/poems/poem/').status_code, 200)
        self.assertEqual(self.client.get('/admin/poems/poem/add/').status_code, 403)

    def test_authorized_draft_preview_is_private(self):
        user = User.objects.create_superuser('editor', 'editor@example.com', 'secure-test-password')
        self.client.force_login(user)
        response = self.client.get(reverse('poems:preview', args=[self.draft.pk]))
        self.assertContains(response, 'Staff preview')
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertEqual(response['X-Robots-Tag'], 'noindex, nofollow')
        self.assertContains(self.client.get('/admin/'), 'Library at a glance')

    def test_bulk_publish_rejects_missing_rights(self):
        self.draft.rights_confirmed = False; self.draft.save()
        user = User.objects.create_superuser('publisher', 'publisher@example.com', 'secure-test-password')
        self.client.force_login(user)
        self.client.post('/admin/poems/poem/', {'action': 'publish', '_selected_action': [str(self.draft.pk)]})
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, 'draft')

class ModelAndUploadTests(LibraryFixture):
    def test_unique_slug_database_constraint(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_poem('Another', self.sun.slug, self.en, 'Duplicate')

    def test_unique_language_code_constraint(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Language.objects.create(name='Duplicate', native_name='Duplicate', code='en', slug='duplicate')

    def test_new_language_needs_no_application_change(self):
        language = Language.objects.create(name='Konkani', native_name='कोंकणी', code='kok', slug='konkani')
        poem = self.make_poem('New language poem', 'konkani-demo', language, 'नवी कविता')
        self.assertContains(self.client.get(language.get_absolute_url()), poem.title)

    def test_published_slug_is_permanent_after_unpublish(self):
        self.sun.status = 'draft'; self.sun.save()
        self.sun.slug = 'different-url'
        with self.assertRaises(ValidationError):
            self.sun.save()

    def test_publication_history_cannot_be_erased(self):
        self.sun.status = 'draft'; self.sun.published_at = None
        with self.assertRaises(ValidationError):
            self.sun.save()

    def test_automatic_slugs_support_non_latin_and_duplicates(self):
        poems = [self.make_poem('कविता', '', self.hi, 'एक कविता') for _ in range(2)]
        self.assertNotEqual(poems[0].slug, poems[1].slug)
        self.assertTrue(poems[0].slug.startswith('poem-'))

    def test_publication_requires_rights(self):
        self.draft.rights_confirmed = False; self.draft.status = 'published'
        with self.assertRaises(ValidationError):
            self.draft.save()

    def test_database_blocks_invalid_published_record(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Poem.objects.filter(pk=self.draft.pk).update(status='published', rights_confirmed=False)

    def test_publication_date_is_set_automatically(self):
        self.draft.published_at = None; self.draft.status = 'published'; self.draft.save()
        self.assertIsNotNone(self.draft.published_at)

    def test_image_extension_and_content_validation(self):
        for name, content in [('unsafe.svg', b'<svg/>'), ('fake.png', b'<script>bad</script>')]:
            with self.assertRaises(ValidationError):
                validate_image(SimpleUploadedFile(name, content))
        buffer = io.BytesIO(); Image.new('RGB', (10, 10)).save(buffer, 'PNG')
        validate_image(SimpleUploadedFile('safe.png', buffer.getvalue()))

    def test_audio_upload_validation(self):
        for name, content in [('test.html', b'ID3text'), ('fake.mp3', b'<script>bad</script>')]:
            with self.assertRaises(ValidationError):
                validate_audio(SimpleUploadedFile(name, content))

    def test_audio_upload_size(self):
        audio = SimpleUploadedFile('large.mp3', b'ID3x')
        audio.size = 21 * 1024 * 1024
        with self.assertRaises(ValidationError):
            validate_audio(audio)

    def test_video_allowlist(self):
        validate_video_url('https://youtu.be/dQw4w9WgXcQ')
        self.assertEqual(youtube_id('https://www.youtube.com/watch?v=dQw4w9WgXcQ'), 'dQw4w9WgXcQ')
        for url in ['javascript:alert(1)', 'http://youtu.be/dQw4w9WgXcQ', 'https://youtube.com.evil.test/watch?v=dQw4w9WgXcQ', 'https://user:pass@youtube.com/watch?v=dQw4w9WgXcQ', 'https://youtube.com:bad/watch?v=dQw4w9WgXcQ', 'https://unknown.test/video.mp4']:
            with self.subTest(url=url), self.assertRaises(ValidationError):
                validate_video_url(url)
        with override_settings(EXTERNAL_VIDEO_HOSTS=['media.example.test']):
            validate_video_url('https://media.example.test/video.mp4')

@override_settings(STORAGES={'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'}, 'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}})
class SeedTests(TestCase):
    def test_seed_is_idempotent_and_preserves_edits(self):
        output = io.StringIO()
        call_command('seed_demo', stdout=output)
        self.assertEqual(Poem.objects.count(), 16)
        self.assertEqual(Language.objects.count(), 13)
        self.assertEqual(ClassLevel.objects.count(), 6)
        poem = Poem.objects.first(); poem.title = 'Edited by a teacher'; poem.save()
        call_command('seed_demo', stdout=output)
        self.assertEqual(Poem.objects.count(), 16)
        poem.refresh_from_db(); self.assertEqual(poem.title, 'Edited by a teacher')
        self.assertTrue(Poem.objects.get(slug='pocketful-of-sunshine').audio_file)
