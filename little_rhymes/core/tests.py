import io
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import TestCase, RequestFactory, override_settings

from .models import SiteSettings
from .security import client_ip
from .views import health, server_error

class SiteInfrastructureTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_settings_are_a_singleton(self):
        SiteSettings.objects.create(site_name='First')
        setting = SiteSettings.objects.first(); setting.site_name = 'Updated'; setting.save()
        self.assertEqual(SiteSettings.objects.count(), 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            SiteSettings.objects.bulk_create([SiteSettings(pk=2, site_name='Not allowed')])

    def test_navigation_cache_invalidated_on_update(self):
        setting = SiteSettings.objects.create(site_name='First Name')
        self.assertContains(self.client.get('/'), 'First Name')
        setting.site_name = 'Updated Name'; setting.save()
        self.assertContains(self.client.get('/'), 'Updated Name')

    def test_untrusted_forwarded_header_ignored(self):
        request = RequestFactory().get('/', REMOTE_ADDR='192.0.2.1', HTTP_X_FORWARDED_FOR='203.0.113.1')
        with override_settings(TRUST_RENDER_PROXY=False):
            self.assertEqual(client_ip(request), '192.0.2.1')

    def test_trusted_proxy_uses_last_valid_hop(self):
        request = RequestFactory().get('/', REMOTE_ADDR='192.0.2.1', HTTP_X_FORWARDED_FOR='untrusted-value, 203.0.113.5')
        with override_settings(TRUST_RENDER_PROXY=True):
            self.assertEqual(client_ip(request), '203.0.113.5')

    def test_invalid_client_address_is_not_used(self):
        request = RequestFactory().get('/', REMOTE_ADDR='invalid')
        self.assertIsNone(client_ip(request))

    def test_health_failure_does_not_leak_details(self):
        request = RequestFactory().get('/health/')
        with patch('core.views.connection.cursor', side_effect=RuntimeError('private connection string')):
            response = health(request)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b'private connection string', response.content)

    def test_500_page_does_not_need_database(self):
        with patch('core.context_processors.SiteSettings.objects.first', side_effect=RuntimeError('database unavailable')):
            response = server_error(RequestFactory().get('/'))
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'Our little library needs a moment.', response.content)

    def test_failed_admin_login_is_limited(self):
        User.objects.create_user('protected-editor', password='private-test-password', is_staff=True)
        self.client.get('/admin/login/')
        for _ in range(5):
            response = self.client.post('/admin/login/', {'username': 'protected-editor', 'password': 'wrong-password'})
        self.assertEqual(response.status_code, 429)

class ProductionConfigurationTests(TestCase):
    """Validate fail-closed startup without connecting to any live cloud services."""
    def configuration_result(self, **changes):
        import os
        import secrets
        import subprocess
        import sys
        from django.conf import settings
        env = os.environ.copy()
        env.update(DEBUG='False', SECRET_KEY=secrets.token_urlsafe(64),
                   ALLOWED_HOSTS='rhymes.example.test', SITE_URL='https://rhymes.example.test',
                   DATABASE_URL='postgresql://validation:validation@127.0.0.1:5432/validation',
                   REDIS_URL='redis://127.0.0.1:6379/15', USE_S3='True',
                   AWS_STORAGE_BUCKET_NAME='not-a-real-bucket',
                   MEDIA_ORIGINS='https://not-a-real-bucket.s3.ap-south-1.amazonaws.com')
        env.update(changes)
        return subprocess.run([sys.executable, '-c', 'import config.settings'], cwd=settings.BASE_DIR,
                              env=env, capture_output=True, text=True, timeout=10)

    def test_valid_production_configuration_imports(self):
        result = self.configuration_result()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_production_rejects_missing_secret(self):
        self.assertNotEqual(self.configuration_result(SECRET_KEY='').returncode, 0)

    def test_render_generated_secret_is_supported(self):
        import base64
        import secrets
        seed = base64.b64encode(secrets.token_bytes(32)).decode('ascii')
        self.assertEqual(len(seed), 44)
        result = self.configuration_result(SECRET_KEY=seed)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_short_or_invalid_base64_secret_is_rejected(self):
        self.assertNotEqual(self.configuration_result(SECRET_KEY='too-short').returncode, 0)
        self.assertNotEqual(self.configuration_result(SECRET_KEY='x'*44).returncode, 0)

    def test_production_rejects_sqlite(self):
        self.assertNotEqual(self.configuration_result(DATABASE_URL='sqlite:///unsafe.sqlite3').returncode, 0)

    def test_production_rejects_local_media(self):
        self.assertNotEqual(self.configuration_result(USE_S3='False').returncode, 0)

    def test_production_rejects_missing_shared_rate_limit_store(self):
        self.assertNotEqual(self.configuration_result(REDIS_URL='').returncode, 0)

    def test_production_rejects_http_site_origin_and_wildcard_host(self):
        self.assertNotEqual(self.configuration_result(SITE_URL='http://rhymes.example.test').returncode, 0)
        self.assertNotEqual(self.configuration_result(ALLOWED_HOSTS='*').returncode, 0)

    def test_production_rejects_missing_or_invalid_media_origin(self):
        self.assertNotEqual(self.configuration_result(MEDIA_ORIGINS='').returncode, 0)
        self.assertNotEqual(self.configuration_result(MEDIA_ORIGINS='https://cdn.example.test/a/path').returncode, 0)
