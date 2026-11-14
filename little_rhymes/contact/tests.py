import io
from datetime import timedelta
from django.core import signing
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, TestCase
from django.utils import timezone
from .models import ContactMessage

class ContactTests(TestCase):
    def setUp(self):
        cache.clear()
        self.payload = {'name': 'A Parent', 'email': 'adult@example.com', 'subject': 'Reading together',
                        'message': 'Thank you for these lovely original classroom poems.',
                        'adult_confirmation': 'on', 'website': '',
                        'form_token': signing.dumps('contact', salt='contact-form')}

    def test_contact_get(self):
        self.assertContains(self.client.get('/contact/'), 'Grown-ups only, please')

    def test_valid_adult_message_saved(self):
        response = self.client.post('/contact/', self.payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertEqual(ContactMessage.objects.first().email, 'adult@example.com')

    def test_invalid_email_and_short_message(self):
        self.payload.update(email='bad', message='tiny')
        self.assertEqual(self.client.post('/contact/', self.payload).status_code, 400)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_adult_confirmation_required(self):
        self.payload.pop('adult_confirmation')
        self.assertEqual(self.client.post('/contact/', self.payload).status_code, 400)

    def test_honeypot_rejects_spam(self):
        self.payload['website'] = 'spam.example'
        self.assertEqual(self.client.post('/contact/', self.payload).status_code, 400)
        self.assertFalse(ContactMessage.objects.exists())

    def test_tampered_token(self):
        self.payload['form_token'] = 'invalid'
        self.assertEqual(self.client.post('/contact/', self.payload).status_code, 400)

    def test_rate_limit_includes_invalid_attempts(self):
        for _ in range(5):
            self.client.post('/contact/', {})
        response = self.client.post('/contact/', self.payload)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response['Retry-After'], '900')
        self.assertFalse(ContactMessage.objects.exists())

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.get('/contact/')
        self.assertEqual(client.post('/contact/', self.payload).status_code, 403)
        self.payload['csrfmiddlewaretoken'] = client.cookies['csrftoken'].value
        self.assertEqual(client.post('/contact/', self.payload).status_code, 302)

    def test_oversized_contact_rejected(self):
        self.payload['message'] = 'a' * 4001
        self.assertEqual(self.client.post('/contact/', self.payload).status_code, 400)

    def test_contact_response_not_cached(self):
        response = self.client.get('/contact/')
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertEqual(response['X-Robots-Tag'], 'noindex, nofollow')

    def test_retention_deletes_only_resolved_old_messages(self):
        old = ContactMessage.objects.create(name='Parent', email='p@example.com', subject='old', message='Resolved old request', is_resolved=True)
        unresolved = ContactMessage.objects.create(name='Parent', email='p@example.com', subject='pending', message='Unresolved old request')
        ContactMessage.objects.filter(pk__in=[old.pk, unresolved.pk]).update(created_at=timezone.now()-timedelta(days=100))
        output = io.StringIO()
        call_command('purge_contacts', dry_run=True, stdout=output)
        self.assertEqual(ContactMessage.objects.count(), 2)
        call_command('purge_contacts', stdout=output)
        self.assertEqual(list(ContactMessage.objects.values_list('pk', flat=True)), [unresolved.pk])
